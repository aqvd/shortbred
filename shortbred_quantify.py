#!/usr/bin/env python

import sys
import argparse
import subprocess
import csv
import re
import os
import datetime

import Bio
from Bio.Seq import Seq
from Bio import SeqIO

parser = argparse.ArgumentParser(description='ShortBRED Quantify \n This program takes a set of protein family markers and wgs file as input, and produces a relative abundance table.')

#Input
parser.add_argument('--markers', type=str, dest='sMarkers', help='Enter the path and name of the genes of interest file (proteins).')
parser.add_argument('--wgs', type=str, dest='sWGS', help='Enter the path and name of the genes of interest file (proteins).')

#Output
parser.add_argument('--results', type=str, dest='sResults', help='Enter the path and name of the results file.')
parser.add_argument('--blastout', type=str, dest='strBlast', help='Enter the path and name of the blastoutput.')

 

#Parameters
parser.add_argument('--id', type=float, dest='dID', help='Enter the percent identity for the match', default = .95)
parser.add_argument('--cov', type=float, dest='dCov', help='Enter the percent coverage for the match', default = .90)


parser.add_argument('--tmp', type=str, dest='sTmp', default =os.getcwd() +os.sep + "tmp",help='Enter the path and name of the tmp directory.')
parser.add_argument('--length', type=int, dest='iLength', help='Enter the minimum length of the markers.')
parser.add_argument('--threads', type=int, dest='iThreads', help='Enter the number of CPUs available for usearch.')
parser.add_argument('--notmarkers', type=str, dest='strNM',default="N", help='.')

#DB Note - Maybe ask Nicola how to remove usearch6 output


args = parser.parse_args()

dirTmp = args.sTmp

log = open(dirTmp + os.sep +"Quantlog.txt", "w")
log.write("ShortBRED log \n" + datetime.date.today().ctime() + "\n SEARCH PARAMETERS \n")
log.write("Match ID:" + str(args.dID) + "\n")
log.write("Match Coverage of Read:" + str(args.dCov) + "\n")
log.close()

###############################################################################
# SUM TOTAL MARKER LENGTH FOR EACH PROT FAMILY

dictMarkerLen = {}

#Load the WGS data. For each gene stub, copy in all the matching genes
for seq in SeqIO.parse(args.sMarkers, "fasta"):
	if args.strNM=="N":
		mtchStub = re.search(r'(.*)_(.M)[0-9]*_\#([0-9]*)',seq.id)
		strStub = mtchStub.group(1)
	else:
		strStub = seq.id
	dictMarkerLen[strStub] = len(seq) + dictMarkerLen.get(strStub,0)   
    

###############################################################################
#USE USEARCH, CHECK WGS NUCS AGAINST MARKER DB

#Make a database from the markers

strDBName = args.sMarkers + ".udb"
strSearchResults = args.sMarkers +".blast"

#Note: Cannot limit threads used in creating of usearch database
p = subprocess.check_call(["usearch6", "--makeudb_usearch", args.sMarkers, "--output", strDBName])


#Use usearch to check for hits (usearch local)
subprocess.check_call(["usearch6", "--usearch_local", args.sWGS, "--db", strDBName, "--id", str(args.dID), "--cov", str(args.dCov),"--blast6out", args.strBlast,"--threads", str(args.iThreads)])


#Go through the blast hits, for each prot family, print out the number of hits
dictBLAST = {}    
for aLine in csv.reader( open( strSearchResults), csv.excel_tab ):
	#print aLine[1]
	if args.strNM=="N":
		mtchProtStub = re.search(r'(.*)_(.M)[0-9]*_\#([0-9]*)',aLine[1])    
		strProtFamily = mtchProtStub.group(1)
	else:
		strProtFamily = aLine[1]
	dictBLAST.setdefault(strProtFamily,set()).add((aLine[0]))
	
    
for strProt in dictBLAST.keys():
    print strProt + "\t" +  str(float(len(dictBLAST[strProt]))/dictMarkerLen[strProt])
    
