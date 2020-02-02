# PyVote

A hackathon python script to simulate alternative ranked voting systems based on
results from Google Forms CSV outputs.

Voting Systems simulated:
- Instant-Runoff Voting
- Two-Round
- Borda Count

election.py will bring up a GUI to select the CSV file, and will output one PDF 
(for each voting system) in the same directory to display plots for each round of voting

FormCreator.gs is a Google App Script to generate the Google Form for a ranked ballot.
The script runs on a Google Sheets document with the following form:

| \<Election name\> |
|-----------------|
| Candidate 1     |
| Candidate 2     |
| Candidate 3     |
| etc.            |
