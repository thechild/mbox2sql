# Example of the use of threadMessages module

import mailbox
import os

import threadMessages

def printRecurse(node,depth=0):
  for message in node.messages:
    print "  "*depth+message.get("subject")
  for child in node.children:
    printRecurse(child,depth+1)
  return None

def printSubjects(listOfTrees):
  for tree in listOfTrees:
    printRecurse(tree)
  return None


def main(m):
  t=threadMessages.jwzThread(m)
  printSubjects(t)
  return None

if __name__=="__main__":
  main()
