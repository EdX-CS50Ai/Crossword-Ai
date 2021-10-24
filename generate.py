import sys

from crossword import *

import random

class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        for v, words in self.domains.items():
            for word in list(words):
                if len(word) != v.length:
                    self.domains[v].remove(word)
            # print(f"enforce node consistency - {v} {self.domains[v]}")

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        if self.crossword.overlaps[x, y] is None:
            return False

        revised = False
        # convert to list during iteration else modifying value will throw
        # RuntimeError: Set changed during iteration
        for word_x in list(self.domains[x]):
            # assume x, y ALWAYS overlaps so no check here - if otherwise, needs check
            i, j = self.crossword.overlaps[x, y]
            corresponding_value = False
            # check that there is corresponding word in y for current word in x
            for word_y in self.domains[y]:
                # print(
                    # f"word_x {word_x} word_y {word_y} i, j {i}, {j} match {word_x[i]} {word_y[j]} {word_x[i] == word_y[j]}"
                    # )
                if word_x[i] == word_y[j]:
                    corresponding_value = True     
            # if no corresponding value found, remove word from x domain
            if not corresponding_value:
                # print(f"{word_x} removed from var {x}")
                self.domains[x].remove(word_x)
                # set revised True as flag to check arc consistency x  
                revised == True
        
        return revised


    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        # generate list of all arcs(overlapping variables) if none provided
        if arcs is None:
            arcs = set()
            for x in self.domains:
                for y in self.crossword.neighbors(x):
                    arcs.add((x, y))

        while len(arcs) > 0:
            x, y = arcs.pop()
            # make the arc consistent, if necessary
            if self.revise(x, y) == True:
                # variable x was revised, add arcs of (x's neighbor, x) to check for consistency 
                for neighbor_variable in self.crossword.neighbor(x):
                    if neighbor_variable != y:
                        arcs.add((neighbor_variable, x))
        # for v in self.domains.keys():
        #     print(f"ac3 - {v} {[word for word in self.domains[v]]}")

        # check for any empty domain values 
        for domain in self.domains.values():
            if domain is set():
                return False
        
        return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        # all variables are assigned
        if len(assignment) == len(self.domains):
            print(f"len assignment {len(assignment)} len domain {len(self.domains)}")
            # # each variable has a value
            # for var, word in assignment.items():
            #     if len(word) == 0:
            #         return False
            return True
        return False

        # # interpret above as all crossword variables must have a value to be complete 
        # for var in self.domains:
        #     if var in assignment:
        #         # variable in assignment but no word assigned, not complete
        #         if assignment[var] is None or len(assignment[var]) == 0:
        #             return False
        #     else:
        #         # this variable has not been added to assignment, so incomplete
        #         return False

        # return True    


    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """

        assigned_words = []

        # assume only one word assument per variable assignment
        for var, word in assignment.items():
            # consistent assignment must be distinct
            if word in assigned_words:
                return False
            # add to track assigned words    
            assigned_words.append(word)
            
            # be correct length
            if len(word) != var.length:
               return False

            # no conflicting neighbor
            for neighbor in self.crossword.neighbors(var):
                # only check assigned neighbors
                if neighbor in assignment:    
                    i, j = self.crossword.overlaps[var, neighbor]
                    if word[i] != assignment[neighbor][j]:
                        return False

        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        assigned_words = [word for word in assignment.values()]

        for word in assigned_words:
            print(f"assigned words {word}")
        unassigned_words = [ word for word in self.domains[var] 
                                if word not in assigned_words ]

        for word in unassigned_words:
            print(f"unassigned words {word}")

        if len(unassigned_words) == 0:
            return None

        # dictionary to keep count of neighbor word conflicts 
        num_of_val_ruled_out = {
            word: 0 
            for word in unassigned_words
        }

        # for each word, loop through neighbor variable words and increment by 1
        # each time the word in the neighbor domain is inconsistent at their overlap 
        # location (i, j) 

        # increment non-assigned neighbor conflicts
        for word in unassigned_words:

            # check overlapping variable word values do not conflict (should be same)
            # for each neighbor, check each word in domain and increment dictionary 
            # if conflict 
            for neighbor in self.crossword.neighbors(var):
                # only consider unassigned neighbors
                if neighbor not in assignment:
                    i, j = self.crossword.overlaps[var, neighbor]
                    for neighbor_word in self.domains[neighbor]:
                        # don't increment if neighbor word is same as current word or if neighbor word is already assigned                    
                        if word[i] != neighbor_word[j] and neighbor_word != word and neighbor_word not in assigned_words:
                            num_of_val_ruled_out[word] += 1  

        ordered_unassigned_domain = [
            word for word, _ in sorted(
                num_of_val_ruled_out.items(),
                key = lambda item: item[1]
            )
        ]

        return ordered_unassigned_domain

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """

        # get unassigned variables 
        unassigned_vars = { var: self.domains[var] 
                    for var, words in self.domains.items() if var not in assignment }
        for k, v in unassigned_vars.items():
            print(f"unassigned k and v {k} {v}")
        if unassigned_vars == {}:
            return None

        # order variables by domain word count (remaining values)
        ordered_by_domain_count = {
            var: len(words) for var, words in sorted(
                unassigned_vars.items(),
                key = lambda item: len(item[1])
            )
        }

        # check if multiple variables have matching lowest domain count value
        lowest = min([
            count 
            for count in ordered_by_domain_count.values() ])
        
        lowest_ordered_domain_count_variables = [
            var for var, count in ordered_by_domain_count.items() 
            if count == lowest
        ]

        by_neighbor_variables = { var: len(self.crossword.neighbors(var)) 
            for var in lowest_ordered_domain_count_variables }

        highest = max([n for var, n in by_neighbor_variables.items()])
        
        for var, count in by_neighbor_variables.items():
            if count == highest:
                return var


    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        print(f"assignment complete {self.assignment_complete(assignment)}")

        # assignment is complete, return it
        if self.assignment_complete(assignment):
            return assignment
        
        # get unassigned variable
        var = self.select_unassigned_variable(assignment)

        # # no unassigned variables and assignment not complete, no solution
        # if var is None and not self.assignment_complete(assignment):
        #     return None

        # order words in domain according to heuristic
        ordered_words = self.order_domain_values(var, assignment)

        # # no words available in domain        
        # if ordered_words is None:
        #     return None

        for word in ordered_words:
            # assign word to variable
            assignment[var] = word
            # check for consistency 
            if self.consistent(assignment):
                for var, word in assignment.items():
                    print(f"consistent assignment var: word {var}: {word}")
                return self.backtrack(assignment)            

        


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
