import matplotlib.pyplot as plt

import random

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

round = {"Chocolate": 4, "Chocolate Peanut Butter": 2, "Cookie Dough": 8, "Cookies and Cream": 1, "Mint Chocolate Chip": 5,  "Moose Tracks": 1,  "Pistachio": 2, "Strawberry": 1, "Vanilla": 4}
names = list(round.keys())
values = list(round.values())

def getColors(n):
    colors = []

    for i in range(0,n):
        colors.append(generate_new_color(colors,pastel_factor = 0.5))
        
    return colors

def graphRound(round):
    
    sortedCandidates = sorted(round.keys(), key=lambda x: round[x], reverse=False)
    sortedCounts = [round[candidate] for candidate in sortedCandidates]
    plt.barh(range(len(round)),sortedCounts,tick_label=sortedCandidates, color=getColors(len(sortedCandidates)))
    
    
    totalVotes = sum(round.values())
    votesNeeded = (totalVotes // 2) + 1

    plt.axvline(x=votesNeeded)
    
    plt.savefig('bar.png')
    plt.show()

graphRound(round)