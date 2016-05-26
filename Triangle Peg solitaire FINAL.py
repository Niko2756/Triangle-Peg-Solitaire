#Niko Lim
#Tuesday, May 24, 2016
def main():
    points,userName = loadPreviousScore()
    while True:
        rows = inputHowManyRows()
        numOfPegs = int((rows*(rows+1))/2)
        pegHoleValue = [1]*numOfPegs
        leftNumber,rightNumber,theBoard,numberCount = cartesianTriangle(rows)
        outputBoardCheck(pegHoleValue,numberCount,rows)
        removeStartPeg = startGameQuestion(numOfPegs)
        pegHoleValue = startingPeg(pegHoleValue,removeStartPeg)
        outputBoardCheck(pegHoleValue,numberCount,rows)
        points = theGamePart(pegHoleValue,numOfPegs,leftNumber,rightNumber,theBoard,numberCount,points,removeStartPeg,rows)
        restart = restartMaybe()
        if restart in ("no","n"):
            print()
            print()
            continue            
        elif restart in ("yes","y"):
            saveScore(points,userName)
            print("Thank you so much for playing. This game has been coded by Niko.")
            break            
        else:
            return restart

def theGamePart(pegHoleValue,numOfPegs,leftNumber,rightNumber,theBoard,numberCount,points,removeStartPeg,rows):
    while True:
        selectedPeg,selectedEmptyHole,middlePeg = selecting(pegHoleValue,numOfPegs,leftNumber,rightNumber,theBoard)
        pegHoleValue = removeMiddlePeg(middlePeg,pegHoleValue,selectedPeg,selectedEmptyHole)
        possibleMovesLeft = isThereAnyMore(pegHoleValue,leftNumber,rightNumber,theBoard)
        if possibleMovesLeft > 0:
            outputBoardCheck(pegHoleValue,numberCount,rows)
            print(possibleMovesLeft,"Possible move choices remaining.")
            continue
        elif possibleMovesLeft == 0:
            print("\nThere are no more possible moves\n")
            points = scoring(points,pegHoleValue,removeStartPeg)
            break          
    return points

def inputHowManyRows():
    while True:
        try:
            rows = int(input("How many rows do you want to play? (or press enter for default): ")or 5)
        except ValueError:
            print("""Hey I don't think that's even a number. \nGo ahead and enter the number of rows again,\nbut make sure it's like a actual number this time:\n\n""")
            continue
        if rows < 4:
            print("Any board below 4 rows is not solvable.")
            continue
        else:
            return rows

def cartesianTriangle(rows):
    leftNumber = []
    rightNumber = []
    theBoard = []
    numberCount = []
    for num in range(rows):
        for x in range(num+1):
            leftNumber.append(x)
            rightNumber.append(num)
    for i in range(len(leftNumber)):
        theBoard.append("{},{}".format(leftNumber[i],rightNumber[i]))
        numberCount.append(i)
    return leftNumber,rightNumber,theBoard,numberCount

def triangleOutput(pegHoleValue,numberCount,rows):
    cen = 80
    num1 = 0
    num2 = 0
    for num in range(rows):
        num1 += num
        num2 += num + 1
        print(str(pegHoleValue[num1:num2]).center(cen))
    print()
    num1 = 0
    num2 = 0
    for num in range(rows):
        num1 += num
        num2 += num + 1
        print(str(numberCount[num1:num2]).center(cen))

def outputBoardCheck(pegHoleValue,numberCount,rows):
    print()
    triangleOutput(pegHoleValue,numberCount,rows)
    print()

def startGameQuestion(numOfPegs):
    while True:
        try:
            removeStartPeg = int(input("Pick the one peg to remove: "))
        except ValueError:
            print("""Hey I don't think that's even a number. \nGo ahead and enter the number again,\nbut make sure it's like a actual number this time:\n\n""")
            continue  
        if not 0 <= removeStartPeg <= numOfPegs:
            print("Please enter a peg between 0 and ",numOfPegs,".")
            continue
        else:
            return removeStartPeg

def startingPeg(pegHoleValue,removeStartPeg):
    pegHoleValue[removeStartPeg] = 0
    return pegHoleValue

def selecting(pegHoleValue,numOfPegs,leftNumber,rightNumber,theBoard):
    while True:
        selectedPeg = movingPeg(pegHoleValue,numOfPegs)
        selectedEmptyHole,middlePeg = movingPegTo(pegHoleValue,numOfPegs,selectedPeg,leftNumber,rightNumber,theBoard)
        if middlePeg == -1:
            continue            
        else:
            return selectedPeg,selectedEmptyHole,middlePeg

def movingPeg(pegHoleValue,numOfPegs):
    while True:
        try:
            selectedPeg = int(input("Pick the one peg to move: "))
        except ValueError:
            print("""Hey I don't think that's even a number. \nGo ahead and enter the number again,\nbut make sure it's like a actual number this time:\n\n""")
            continue  
        if not 0 <= selectedPeg <= numOfPegs:
            print("Please enter a peg between 0 and ",numOfPegs,".")
            continue
        elif pegHoleValue[selectedPeg] == 0:
            print("There is no peg there. Please select a hole with a peg again.")
            continue
        else:
            return selectedPeg

def movingPegTo(pegHoleValue,numOfPegs,selectedPeg,leftNumber,rightNumber,theBoard):
    while True:
        try:
            selectedEmptyHole = int(input("Pick the one to move your selected peg to: "))
        except ValueError:
            print("""Hey I don't think that's even a number. \nGo ahead and enter the number again,\nbut make sure it's like a actual number this time:\n\n""")
            continue  
        if not 0 <= selectedEmptyHole <= numOfPegs:
            print("Please enter a peg between 0 and ",numOfPegs,".")
            continue
        elif pegHoleValue[selectedEmptyHole] == 1:
            print("Please select a hole without a peg.")
            continue
        middlePeg = whatIsTheMiddlePeg(selectedPeg,selectedEmptyHole,leftNumber,rightNumber,theBoard)
        if middlePeg == -1:
            yesOrNo = yesOrNoSelection()
            if yesOrNo in ("yes","y"):
                continue            
            elif yesOrNo in ("no","n"):
                return selectedEmptyHole,middlePeg
                break
        else:
            return selectedEmptyHole,middlePeg

def whatIsTheMiddlePeg(selectedPeg,selectedEmptyHole,leftNumber,rightNumber,theBoard):
    middlePeg = -1
    if leftNumber[selectedPeg] == leftNumber[selectedEmptyHole]:
        if rightNumber[selectedPeg] == rightNumber[selectedEmptyHole]+2:
            middlePeg = theBoard.index("{},{}".format(leftNumber[selectedPeg],rightNumber[selectedPeg]-1))
        elif rightNumber[selectedPeg] == rightNumber[selectedEmptyHole]-2:
            middlePeg = theBoard.index("{},{}".format(leftNumber[selectedPeg],rightNumber[selectedPeg]+1))
    elif rightNumber[selectedPeg] == rightNumber[selectedEmptyHole]:
        if leftNumber[selectedPeg] == leftNumber[selectedEmptyHole]+2:
            middlePeg = theBoard.index("{},{}".format(leftNumber[selectedPeg]-1,rightNumber[selectedPeg]))
        elif leftNumber[selectedPeg] == leftNumber[selectedEmptyHole]-2:
            middlePeg = theBoard.index("{},{}".format(leftNumber[selectedPeg]+1,rightNumber[selectedPeg]))
    elif (leftNumber[selectedPeg]+2,rightNumber[selectedPeg]+2) == (leftNumber[selectedEmptyHole],rightNumber[selectedEmptyHole]):
        middlePeg = theBoard.index("{},{}".format(leftNumber[selectedPeg]+1,rightNumber[selectedPeg]+1))
    elif (leftNumber[selectedPeg],rightNumber[selectedPeg]) == (leftNumber[selectedEmptyHole]+2,rightNumber[selectedEmptyHole]+2):
        middlePeg = theBoard.index("{},{}".format(leftNumber[selectedPeg]-1,rightNumber[selectedPeg]-1))
    return middlePeg

def isThereAnyMore(pegHoleValue,leftNumber,rightNumber,theBoard):
    possibleMovesLeft = 0
    for num in range(len(pegHoleValue)):
        if pegHoleValue[num] == 1:
            try:
                if pegHoleValue[theBoard.index("{},{}".format(leftNumber[num],rightNumber[num]+1))] == 1:
                    if pegHoleValue[theBoard.index("{},{}".format(leftNumber[num],rightNumber[num]+2))] == 0:
                        possibleMovesLeft += 1
            except ValueError:
                pass
            try:
                if pegHoleValue[theBoard.index("{},{}".format(leftNumber[num]+1,rightNumber[num]+1))] == 1:
                    if pegHoleValue[theBoard.index("{},{}".format(leftNumber[num]+2,rightNumber[num]+2))] == 0:
                        possibleMovesLeft += 1
            except ValueError:
                pass
            try:
                if pegHoleValue[theBoard.index("{},{}".format(leftNumber[num]+1,rightNumber[num]))] == 1:
                    if pegHoleValue[theBoard.index("{},{}".format(leftNumber[num]+2,rightNumber[num]))] == 0:
                        possibleMovesLeft += 1
            except ValueError:
                pass
            try:
                if pegHoleValue[theBoard.index("{},{}".format(leftNumber[num]-1,rightNumber[num]))] == 1:
                    if pegHoleValue[theBoard.index("{},{}".format(leftNumber[num]-2,rightNumber[num]))] == 0:
                        possibleMovesLeft += 1
            except ValueError:
                pass
            try:
                if pegHoleValue[theBoard.index("{},{}".format(leftNumber[num]-1,rightNumber[num]-1))] == 1:
                    if pegHoleValue[theBoard.index("{},{}".format(leftNumber[num]-2,rightNumber[num]-2))] == 0:
                        possibleMovesLeft += 1
            except ValueError:
                pass
            try:
                if pegHoleValue[theBoard.index("{},{}".format(leftNumber[num],rightNumber[num]-1))] == 1:
                    if pegHoleValue[theBoard.index("{},{}".format(leftNumber[num],rightNumber[num]-2))] == 0:
                        possibleMovesLeft += 1
            except ValueError:
                pass
    return possibleMovesLeft

def removeMiddlePeg(middlePeg,pegHoleValue,selectedPeg,selectedEmptyHole):
    if pegHoleValue[middlePeg] == 1:
        pegHoleValue[middlePeg] = 0
        pegHoleValue[selectedPeg] = 0
        pegHoleValue[selectedEmptyHole] = 1
    else:
        print("\nHey that peg is already removed\n")
    return pegHoleValue

def scoring(points,pegHoleValue,removeStartPeg):
    if sum(pegHoleValue) > 3 and not int(sum(pegHoleValue)/len(pegHoleValue)*100) > 51:
        points.append(0)
        print("\nGAME OVER: You get no points because that was just ok, not really that good.\n")
    elif sum(pegHoleValue) == 3:
        points.append(10)
        print("\nNice, just so-so, but still nice.\nYou get 10 points.\n")
    elif sum(pegHoleValue) == 2:
        points.append(25)
        print("\nAwesome, you are above average!!! \nYou get 25 points.\n")
    elif sum(pegHoleValue) == 1 and pegHoleValue.index(1) == removeStartPeg:
        points.append(100)
        print("\nWOW, you are brilliant!!!! That was outstandingly astonishing!!!! \nYou get 100 points.\n")
        print("You win, but what you have won is for you to decide and for the rest of us to find out!!!!!\n")
    elif sum(pegHoleValue) == 1:
        points.append(50)
        print("\nFantastic, you are very smart. \nYou get 50 points.\n")
        print("You win, but what you have won is for you to decide and for the rest of us to find out!!!!!\n")
    elif int(sum(pegHoleValue)/len(pegHoleValue)*100) > 51:
        points.append(200)
        print("\nAmazing, you are a genius!!!!! \nYou get 200 points.\n")
        print("You were able to get more than\n50 percent of the pegs still remaining on the board with no moves left well done you.\n")
    print("The score of your previous game was:",points[-2])
    print("Your current total score is:",sum(points))
    return points

def yesOrNoSelection():
    print("\nYou have attempted a move that is not permitted.\n")
    while True:
        yesOrNo = input("\nDo you want to reselect this peg? (yes)\nor start your two recent peg selections over? (no)\n(Enter yes or no): ")
        if yesOrNo.lower() not in ("yes", "no", "y", "n"):
            print("Come on that's not what I asked for.\nPlease just give me a affirmative yes or a no in English please.")
            continue
        else:
            return yesOrNo.lower()

def restartMaybe():
    while True:
        restart = input("\nDo you want to end this program? (Enter yes or no): ")
        if restart.lower() not in ("yes", "no", "y", "n"):
            print("Come on that's not what I asked for.\nPlease just give me a affirmative yes or a no in English please.")
            continue
        else:
            return restart.lower()

def doYouWantToSave():
    while True:
        saveIt = input("\nDo you want to save your score for later? (Enter yes or no): ")
        if saveIt.lower() not in ("yes", "no", "y", "n"):
            print("Come on that's not what I asked for.\nPlease just give me a affirmative yes or a no in English please.")
            continue
        else:
            return saveIt.lower()

def inputName():
    while True:
        userName = input("Enter your name: ")
        if not userName.isalpha() and not userName.isprintable():
            print("Come on that's not what I asked for.\nPlease just give me a name in English please.\n")
            continue
        if userName == "NOUSERNAMEZ":
            print("Come on that's not what I asked for.\nPlease just give me a name in English please.\n")
            continue
        else:
            return userName.capitalize()

def saveScore(points,userName):
    saveIt = doYouWantToSave()
    if saveIt in ("yes","y"):
        if userName == "NOUSERNAMEZ":
            userName = inputName()
        with open("""{}'s Peg Solitaire Score.txt""".format(userName),"w") as outFile:
            for num in range(len(points)):
                outFile.write(str(points[num]) + "\n")
        outFile.close()
        print("Your score has been saved under: " """{}'s Peg Solitaire Score.txt""".format(userName))
    elif saveIt in ("no","n"):
        print("You have decided to not save your score.")
        pass

def doYouWantToResumeScore():
    while True:
        resume = input("\nDo you want to load your score from a previous game session? (Enter yes or no)\nOr you can press ENTER to start a NEW GAME immediately: ") or "no"
        if resume.lower() not in ("yes", "no", "y", "n"):
            print("Come on that's not what I asked for.\nPlease just give me a affirmative yes or a no in English please.")
            continue
        else:
            return resume.lower()

def loadPreviousScore():
    points = []
    resume = doYouWantToResumeScore()
    if resume in ("yes","y"):
        userName = inputName()
        with open("""{}'s Peg Solitaire Score.txt""".format(userName),"r") as outFile:
            for line in outFile:
                points.append(int(line))
        outFile.close()
        print("Your score has been loaded from: " """{}'s Peg Solitaire Score.txt""".format(userName))
    elif resume in ("no","n"):
        points = [0]
        userName = "NOUSERNAMEZ"
    return points,userName

main()
