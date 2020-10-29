# Critical Infrastructure Cyberspace Analysis Tool (CICAT)
CICAT is a modeling and simulation tool for evaluating how an adversary might conduct a cyber attack. CICAT uses a threat model that leverages open source cyber threat data provided by MITRE Enterprise ATT&CK™ and ATT&CK for ICS. MITRE developed CICAT to automate production of cyber attack scenarios in support of International Atomic Energy Agency (IAEA) Coordinated Research Program (CRP) J02008: "Enhancing Computer Security Incident Analysis at Nuclear Facilities", which seeks to improve capabilities to prevent, detect, and respond to cyber security incidents at nuclear facilities.
# Version
CICAT v1.1
# Copyright 2020 The MITRE Corporation. All Rights Reserved. 
Approved for public release; Distribution unlimited. PRS Case 20-2400.
# Licensing
Apache 2.0
# Documentation
A whitepaper discussing CICAT functional capabilities is available at https://www.mitre.org/publications/technical-papers/critical-infrastructure-cyberspace-analysis-tool-cicat-capability.
# Platform requirements
Python 3.7 or better
# Installation
Unzip the distribution
# How to run
This CICAT distribution includes the program scenGEN.py, which is used to generate cyber attack scenarios. This program imports an infrastructure model and scenario specification as Excel spreadsheets, and exports generated scnerarios data as an Excel spreadsdheet. 

To run scenGEN.py: 
python scenGEN.py -i \<infrastucture spreadsheet.xlsx\> -s \<scenario specification.xlsx\> -o \<results spreadsheet.xlsx\>
                                                                                                   
Examples of infrastucture and scenario specification spreadsheets can be found in the data subdirectory and are called TB_infrastructure.xlsx and TB_scnearios.xlsx, respectively. These spreadsheets represent an infrastructure testbed developed for testing purposes. These testbed files are imported by default if scenGEN.py is invoked without -i or -s input parameters.  

The -o parameter is used to specify a filename for the output spreadsheet. If no -o parameter is supplied, the default filename 'Results' is used and saved in the data subdirectory. The output filename is always appended with a timestamp to prevent CICAT from overwriting previous scenario results. 
