import csv, random, json, sys, os, subprocess
import tkinter as tk
from tkinter import filedialog, Text
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf
from pathlib import Path
from copy import deepcopy
from tkinter.font import Font

"""
Data types:

Ballots
Each ballot is a list of candidates, in the order of ranking
    ex. [["First Choice", "Second Choice"], 
        ["First Choice", "Second Choice", "Third Choice"]]

Rounds
Each round is a dictionary mapping each candidate to 
their vote count for that round
    ex. {
            "Option 1": 30,
            "Option 2": 25,
            "Option 3": 11
        }


"""

def lighten_color(color, amount=0.5):
    """
    Lightens the given color by multiplying (1-luminosity) by the given amount.
    Input can be matplotlib color string, hex string, or RGB tuple.

    Examples:
    >> lighten_color('g', 0.3)
    >> lighten_color('#F034A3', 0.6)
    >> lighten_color((.3,.55,.1), 0.5)
    """
    import matplotlib.colors as mc
    import colorsys
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])

def get_random_color(pastel_factor = 0.5):
    return [(x+pastel_factor)/(1.0+pastel_factor) for x in [random.uniform(0,1.0) for i in [1,2,3]]]

def color_distance(c1,c2):
    return sum([abs(x[0]-x[1]) for x in zip(c1,c2)])

def generate_new_color(existing_colors,pastel_factor = 0.5):
    max_distance = None
    best_color = None
    for i in range(0,100):
        color = get_random_color(pastel_factor = pastel_factor)
        if not existing_colors:
            return color
        best_distance = min([color_distance(color,c) for c in existing_colors])
        if not max_distance or best_distance > max_distance:
            max_distance = best_distance
            best_color = color
    return best_color

def getColorList(n):
    colors = []

    for i in range(0,n):
        colors.append(generate_new_color(colors,pastel_factor = 0.1))
        
    return colors

def assignColors(candidates):
    colors = {}
    # Get one color for every candidate
    randomColors = getColorList(len(candidates))
    # Assign each candidate a color
    for i in range(0, len(candidates)):
        candidate = candidates[i]
        color = randomColors[i]
        colors[candidate] = color
    
    return colors

def graphRound(rounds, roundNumber, scores, votingSystem, colors):
    """
    colors: a dictionary mapping candidates to colors
    """

    round = rounds[roundNumber]

    # Hacky thing to clear old figure
    plt.figure(roundNumber)
    plt.clf()
    plt.close(plt.gcf())
    plt.figure(roundNumber)

    plt.title("Round " + str(roundNumber + 1))

    if (votingSystem == "Borda Count"):
        xlabel = "Borda Score"
    else:
        xlabel = "Number of votes"
    
    sortedCandidates = sorted(round.keys(), key=lambda x: (round[x], scores[x]))
    sortedTotalCounts = [round[candidate] for candidate in sortedCandidates]

    colorList = [colors[c] for c in sortedCandidates]

    if roundNumber != 0:
        # If it's not the first round, print new votes to the right of old votes
        previousRound = rounds[roundNumber - 1]
        sortedPreviousCounts = [previousRound[candidate] for candidate in sortedCandidates]
        sortedNewCounts = [t - p for t, p in zip(sortedTotalCounts, sortedPreviousCounts)]

        plt.barh(range(len(round)),sortedPreviousCounts, tick_label=sortedCandidates, edgecolor = "black", color=colorList)
        plt.barh(range(len(round)),sortedNewCounts, tick_label=sortedCandidates, left=sortedPreviousCounts, edgecolor = "black", color=[lighten_color(c) for c in colorList])
         
    else:
        plt.barh(range(len(round)),sortedTotalCounts,tick_label=sortedCandidates, edgecolor = "black", color=colorList)
        
    plt.xlabel(xlabel)

    # Display threshold line
    if (votingSystem != "Borda Count"):
        totalVotes = sum(round.values())
        votesNeeded = (totalVotes // 2) + 1
        plt.axvline(x=votesNeeded)
    
    plt.tight_layout()
    
def roundsToPdf(rounds, pdfFilename, scores, votingSystem, colors=None):

    candidates = list(rounds[0].keys())

    # Randomly select colors
    if colors == None:
        colors = assignColors(candidates)

    for roundNumber in range(0, len(rounds)):
        graphRound(rounds, roundNumber, scores, votingSystem, colors)

    pdf = matplotlib.backends.backend_pdf.PdfPages(pdfFilename)
    for fig in range(0, len(rounds)): ## will open an empty extra figure :(
        pdf.savefig( fig )
    pdf.close()

    subprocess.run(['start', pdfFilename], check=True, shell=True)

def writeJson(object, filename, indent=None, sort_keys=False):
    """Writes a python object to a json file
    Optional arguments are the same as in json.dumps"""
    with open(filename, "w") as outFile:
        outFile.write(json.dumps(object, indent=indent, sort_keys=sort_keys))

def chooseLoser(round, scores):
    """
    Choose the loser of a round, to be eliminated

    Parameters:
    round (dictionary): A dictionary representing the round
    scores (dictionary): A dictionary mapping each candidate to a score
                         (used for tiebreaking)

    Return:
    string: The name of the candidate to eliminate
    """

    # Get a list of all candidates who got the lowest number of votes
    lowestCandidates = [c for c in round if round[c] == min(round.values())]

    # If theres only one with the minimum value, we good
    if len(lowestCandidates) == 1:
        return lowestCandidates[0]

    # Otherwise, we need a tiebreaker

    # Create a new scores dictionary that only has scores from the lowest candidates
    loserScores = {}
    for loserCandidate in lowestCandidates:
        loserScores[loserCandidate] = scores[loserCandidate]

    # Get a list of all loser candidates with the minimum score value
    lowestCandidates = [c for c in loserScores if loserScores[c] == min(loserScores.values())]

    # If theres only one with the minimum value, we good
    if len(lowestCandidates) == 1:
        return lowestCandidates[0]

    # If not, just pick a random number
    return random.choice(lowestCandidates)


def removeCandidate(candidate, ballots):
    """
    Remove a candidate from everyones ballots
    If this removal makes a ballot empty, then remove that ballot

    Parameters:
    candidate(string): The name of the candidate to eliminate
    ballots (list): A list of ballots. 

    Returns:
    list: An updated list of ballots
    """

    for ballot in ballots:
        try:
            ballot.remove(candidate)
        except ValueError:
            # If the candidate isn't on the ballot, that's fine
            pass
    
    # Return all non-empty ballots
    return [b for b in ballots if len(b) != 0]

def getRound(candidates, ballots):
    """
    Runs one round of an IRV election by counting the number of
    current first choices for each candidate

    Parameters:
    candidates (list): A list of candidates
    ballots (list): A list of ballots. 

    Returns:
    round: A dictionary representing the round
    """
    round = {}

    for candidate in candidates:
        round[candidate] = 0

    # Cound the votess
    for ballot in ballots:
        round[ballot[0]] += 1

    return round

def getCandidates(ballots):
    """
    From a list of ballots, returs a list of candidates

    Parameters:
    ballots (list): A list of ballots. 
                    
    Returns:
    list: A list of candidates.
    """
    candidates = set()

    for ballot in ballots:
        for candidate in ballot:
            candidates.add(candidate)

    return list(candidates)

def calculateBordaScores(candidates, ballots):
    """
    Assign each candidate a score based on their ranks in ballots
    (Used for tiebreaking in IRV, and also for the Borda system)
    Each vote for a candidate will add (n - r) to their score,
    where r is the rank (1st, 2nd, 3rd...) and n is the number of candidates - 
    this number is the number of candidates that the given candidate ranked ABOVE

    Parameters:
    candidates (list): A list of candidates
    ballots (list): A list of ballots. 

    Returns:
    dictionary: A mapping of every candidate to their score
    """
    scores = {}
    n = len(candidates)

    for candidate in candidates:
        scores[candidate] = 0
    
    for ballot in ballots:
        for i in range(0, len(ballot)):
            candidate = ballot[i]
            r = i+1
            scores[candidate] += (n - r)

    return scores

def validateBallot(ballot):
    """
    Checks to see if a ballot is valid
    A ballot is valid if the only empty values are at the end of a ballot

    For example, this ballot is valid:
    ['Cookie Dough', 'Mint Chocolate Chip', 'Vanilla', '', '', '', '', '', '']

    But this ballot is invalid:
    ['Vanilla', 'Cookies and Cream', 'Cookie Dough', 'Strawberry', '', '', '', '', 'Chocolate']

    Parameters:
    ballot (list): The unprocessed ballot (empty values haven't been removed)

    Returns:
    boolean: True if the ballot is valid, False if invalid
    """

    # Every ballot must have a first choice
    if (ballot[0] == ""):
        return False

    # Every choice after the first empty choice must also be empty
    # (You can't specify your third choice if you haven't specified your second)
    try:
        firstEmpty = ballot.index("")
        for i in range(firstEmpty, len(ballot)):
            if ballot[i] != "":
                return False
    except ValueError:
        # If there are no empty choices, we all good
        pass

    return True

def readBallots(filename):
    """
    Reads ballots from a csv file, exported from Google Forms
    Also validates ballots and throws out any that are spoiled

    Parameters:
    filename (string): The name of the csv file

    Returns:
    list: A list of ballots. 
    """

    # Read CSV file
    with open(filename, "r") as csvFile:
        rawCsv = list(csv.reader(csvFile, delimiter = ','))

    ballots = []

    # print("Ballots found: " + str(len(rawCsv) - 1))

    # Validate ballots and remove empty space
    for row in rawCsv[1:]:
        ballot = row[1:]
        if validateBallot(ballot):
            ballots.append([candidate for candidate in ballot if candidate != ""])
        # else:
        #     print("Voided ballot: " + str(ballot))

    # print("Valid ballots: " + str(len(ballots)))
    
    return ballots

def roundHasWinner(round):
    """
    Checks if the round is the last round (if one candidate has a majority)

    Parameters:
    round (dictionary): A dictionary representing the round

    Returns:
    boolean: True if round has a winner, false otherwise
    """

    totalVotes = sum(round.values())
    votesNeeded = (totalVotes // 2) + 1

    for candidate in round:
        if round[candidate] >= votesNeeded:
            return True

    return False

def irv(ballots):
    """
    Simulates an irv election

    Parameters:
    ballots (list): A list of ballots. 
                    
    Returns:
    (rounds, scores): A tuple containing the rounds and scores
    """

    candidates = getCandidates(ballots)
    scores = calculateBordaScores(candidates, ballots)
    rounds = []

    # for b in ballots:
    #     print(b)

    currentRound = getRound(candidates, ballots)
    # For the first round: eliminate candidates with 0 votes initially
    zeroCandidates = [c for c in candidates if currentRound[c] == 0]
    for zeroCandidate in zeroCandidates:
        removeCandidate(zeroCandidate, ballots)
        del currentRound[zeroCandidate]
        candidates.remove(zeroCandidate)

    rounds.append(currentRound)

    # As long as the most recent round doesn't have a winner, keep looping
    while(not roundHasWinner(currentRound)):
        # print("--------------- ROUND --------------")
        # for b in ballots:
        #     print(b)
        # print(currentRound)

        # Eliminate a candidate
        loser = chooseLoser(currentRound, scores)
        ballots = removeCandidate(loser, ballots)
        candidates.remove(loser)

        # Run the next round
        currentRound = getRound(candidates, ballots)
        rounds.append(currentRound)

    return (rounds, scores)

def bordaCount(ballots):
    """
    Returns
    (rounds, scores): A tuple containing the rounds and scores
    For this function, returning the scores is redundant, but keeps things consistent
    """
    candidates = getCandidates(ballots)
    scores = calculateBordaScores(candidates, ballots)
    return ([scores], scores)

def twoRound(ballots):
    """
    Simulate a two-round election using ranked ballots

    Returns
    (rounds, scores): A tuple containing the rounds and scores
    """
    candidates = getCandidates(ballots)
    scores = calculateBordaScores(candidates, ballots)
    rounds = []

    # for b in ballots:
    #     print(b)

    firstRound = getRound(candidates, ballots)
    # For the first round: eliminate candidates with 0 votes initially
    zeroCandidates = [c for c in candidates if firstRound[c] == 0]
    for zeroCandidate in zeroCandidates:
        removeCandidate(zeroCandidate, ballots)
        del firstRound[zeroCandidate]
        candidates.remove(zeroCandidate)

    # Append a copy so that the first round can be modified
    rounds.append(firstRound.copy())

    # If theres a winner in the first round, we're done
    if(roundHasWinner(firstRound)):
        return rounds
    
    # Otherwise, eliminate all but the top two candidates
    while(len(candidates) > 2):
        # Eliminate a candidate
        loser = chooseLoser(firstRound, scores)
        ballots = removeCandidate(loser, ballots)
        candidates.remove(loser)
        del firstRound[loser]

    # Run the next round
    secondRound = getRound(candidates, ballots)
    rounds.append(secondRound)

    return (rounds, scores)

def ballotsToPdf(ballots, votingSystem, pdfOutput, colors=None):
    rounds, scores = voteSwitch[votingSystem](ballots)
    roundsToPdf(rounds, pdfOutput, scores, votingSystem, colors=colors)

def getPdfOutputName(csvFile, votingSystem):
    # Remove all spaces from filename so that the os can open it
    return (csvFile.split(".")[0] + "_"  + votingSystem + ".pdf").replace(" ", "_")

def promptFilename(votingSystem):
    csvFile = filedialog.askopenfilename(initialdir=str(Path.home()), title="Select File",
                                         filetypes=(("csv files", "*.csv"), ("all files", "*.*")))

    ballots = readBallots(csvFile)
    
    candidates = getCandidates(ballots)
    colors = assignColors(candidates)

    # Allow the user to specify 'all'
    if (votingSystem == "All"):
        for vs in voteSwitch:
            ballotsToPdf(deepcopy(ballots), vs, getPdfOutputName(csvFile, vs), colors=colors)
    else:
        ballotsToPdf(ballots, votingSystem, getPdfOutputName(csvFile, votingSystem), colors=colors)

voteSwitch = {
    "Instant-Runoff": irv,
    "Borda Count": bordaCount,
    "Two-Round": twoRound,
}

def main():
    
    root = tk.Tk()

    root.config(height=500, width=500)
    root.title("KnowVote")

    bold_font = Font(family="Helvetica", size=12, weight="bold")

    image = tk.PhotoImage(file=os.path.join('images', "KnowVoteLogoSmallT.png"))
    imageLabel = tk.Label(image=image)
    imageLabel.pack(padx=50, pady=10)

    fileSelectPane = tk.Frame(root)
    fileSelectPane.pack(anchor=tk.CENTER, padx = 20, pady = 10)

    # Label
    dropdownLabel = tk.Label(fileSelectPane, text="Select voting system: ", font=bold_font)
    dropdownLabel.grid(row=0, column=0, pady=10)

    # Dropdown
    votingOptions = list(voteSwitch.keys()) + ["All"]

    votingSystemSelection = tk.StringVar(root)
    votingSystemSelection.set(votingOptions[0])

    votingSystemDropdown = tk.OptionMenu(fileSelectPane, votingSystemSelection, *votingOptions) 
    votingSystemDropdown.config(fg="white", activeforeground="white", bg="#D4030B", activebackground="#ED1C24", height=2, font=bold_font)
    votingSystemDropdown.grid(row=0, column=1, padx=10, pady=10)

    # Open file button
    openFile = tk.Button(fileSelectPane, text="Open CSV Ballot File", padx=10, height=2, font=bold_font,
                         fg="white", bg="#2E3192", command=lambda: promptFilename(votingSystemSelection.get()))
    openFile.grid(row=0, column=2, padx=10, pady=10)

    root.mainloop()


if (__name__ == "__main__"):
    main()
    input('Press Enter to Continue...')

    # round = {
    #     "Trump": 60,
    #     "Clinton": 58,
    #     "Jeb": 100,
    # }

    # sortedCandidates = sorted(round.keys(), key=lambda x: round[x], reverse=False)
    # sortedCounts = [round[candidate] for candidate in sortedCandidates]

    # print(sortedData)

