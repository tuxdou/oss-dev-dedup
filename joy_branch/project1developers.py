import csv
import pandas as pd
import unicodedata
import string
from itertools import combinations
from Levenshtein import ratio as sim
import os
import random

# This block of code take the repository, fetches all the commits,
# retrieves name and email of both the author and commiter and saves the unique
# pairs to csv
# If you provide a URL, it clones the repo, fetches the commits and then deletes it,
# so for a big project better clone the repo locally and provide filesystem path

from pydriller import Repository
DEVS = set()
for commit in Repository("https://github.com/facebook/react").traverse_commits():
    DEVS.add((commit.author.name, commit.author.email))
    DEVS.add((commit.committer.name, commit.committer.email))

DEVS = sorted(DEVS)

# ✅ Limit developers to between 500 and 1000 entries
num_devs = len(DEVS)
print(f"Total unique devs found: {num_devs}")

if num_devs > 700:
    DEVS = random.sample(DEVS, 700)
elif num_devs < 500:
    print(f"Only {num_devs} developers found — keeping all for inspection.")

# Ensure folder exists
os.makedirs("project1devs", exist_ok=True)

with open(os.path.join("project1devs", "devs.csv"), 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile, delimiter=',', quotechar='"')
    writer.writerow(["name", "email"])
    writer.writerows(DEVS)


# This block of code reads an existing csv of developers

DEVS = []
# Read csv file with name,dev columns
with open(os.path.join("project1devs", "devs.csv"), 'r', newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        DEVS.append(row)
# First element is header, skip
DEVS = DEVS[1:]


# Function for pre-processing each name,email
def process(dev):
    name: str = dev[0]

    # Remove punctuation
    trans = name.maketrans("", "", string.punctuation)
    name = name.translate(trans)
    # Remove accents, diacritics
    name = unicodedata.normalize('NFKD', name)
    name = ''.join([c for c in name if not unicodedata.combining(c)])
    # Lowercase
    name = name.casefold()
    # Strip whitespace
    name = " ".join(name.split())


    # Attempt to split name into firstname, lastname by space
    parts = name.split(" ")
    # Expected case
    if len(parts) == 2:
        first, last = parts
    # If there is no space, firstname is full name, lastname empty
    elif len(parts) == 1:
        first, last = name, ""
    # If there is more than 1 space, firstname is until first space, rest is lastname
    else:
        first, last = parts[0], " ".join(parts[1:])

    # Take initials of firstname and lastname if they are long enough
    i_first = first[0] if len(first) > 1 else ""
    i_last = last[0] if len(last) > 1 else ""

    # Determine email prefix
    email: str = dev[1]
    prefix = email.split("@")[0]

    return name, first, last, i_first, i_last, email, prefix


# Compute similarity between all possible pairs
SIMILARITY = []
all_pairs = list(combinations(DEVS, 2))
print(f"Total possible pairs: {len(all_pairs)}")

for dev_a, dev_b in all_pairs:
    # Pre-process both developers
    name_a, first_a, last_a, i_first_a, i_last_a, email_a, prefix_a = process(dev_a)
    name_b, first_b, last_b, i_first_b, i_last_b, email_b, prefix_b = process(dev_b)

    # Conditions of Bird heuristic
    c1 = sim(name_a, name_b)
    c2 = sim(prefix_b, prefix_a)
    c31 = sim(first_a, first_b)
    c32 = sim(last_a, last_b)
    c4 = c5 = c6 = c7 = False
    # Since lastname and initials can be empty, perform appropriate checks
    if i_first_a != "" and last_a != "":
        c4 = i_first_a in prefix_b and last_a in prefix_b
    if i_last_a != "":
        c5 = i_last_a in prefix_b and first_a in prefix_b
    if i_first_b != "" and last_b != "":
        c6 = i_first_b in prefix_a and last_b in prefix_a
    if i_last_b != "":
        c7 = i_last_b in prefix_a and first_b in prefix_a

    # Save similarity data for each conditions. Original names are saved
    SIMILARITY.append([dev_a[0], email_a, dev_b[0], email_b, c1, c2, c31, c32, c4, c5, c6, c7])



# Save data on all pairs (might be too big -> comment out to avoid)
cols = ["name_1", "email_1", "name_2", "email_2", "c1", "c2",
        "c3.1", "c3.2", "c4", "c5", "c6", "c7"]
df = pd.DataFrame(SIMILARITY, columns=cols)
# df.to_csv(os.path.join("project1devs", "devs_similarity.csv"), index=False, header=True, encoding='utf-8')


# Set similarity threshold, check c1-c3 against the threshold
t=0.7
print("Threshold:", t)
df["c1_check"] = df["c1"] >= t
df["c2_check"] = df["c2"] >= t
df["c3_check"] = (df["c3.1"] >= t) & (df["c3.2"] >= t)
df_filtered = df[df[["c1_check", "c2_check", "c3_check", "c4", "c5", "c6", "c7"]].any(axis=1)]

#if filtered data is too large, show 7000 max
if len(df_filtered) > 700 :
    df_filtered = df_filtered.sample(700, random_state=42)

#if filtered data is too small, keep 500
elif len(df_filtered) < 500 :
    print(f"Filtered row only {len(df_filtered)}, keeping all for inspection.")

df_filtered = df_filtered[["name_1", "email_1", "name_2", "email_2", "c1", "c2", "c3.1", "c3.2", "c4", "c5", "c6", "c7"]]

df_filtered.to_csv(os.path.join("project1devs", f"devs_similarity_t={t}.csv"), index = False, header=True, encoding="utf-8")


print(f"Final CSV rows: {len(df_filtered)}")
