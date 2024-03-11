"""
swift_scrape.py - a small library of Swift-scraping tools (code by Benjamin Gompertz) 

Change the 'loc' directory path to your desired path. The code will create directories on top of 'loc' for each GRB you request.

Documentation for get_targetIDs, get_xrt, get_xrtdense added by Kruthi Krishna
"""


import numpy as np
import urllib
import os
from astropy.table import Table
from astropy.io import ascii
from urllib.error import HTTPError

loc='./afterglow_data/'


def get_targetIDs(url='https://www.swift.ac.uk/xrt_curves/grb.list',save=True):
    """
    get_targetIDs function populates a lookup table of GRBs vs their target IDs.
    """

	with urllib.request.urlopen(url) as f:
		string = f.read().decode('utf-8').splitlines()
	
	GRB = []
	targetID = []
	
	for line in string:
		GRB = np.append(GRB,line.split()[1])
		targetID = np.append(targetID,line.split()[2])
		
	IDs = Table([GRB,targetID],names=('GRB','targetID'))
	
	if save == True:
		if not os.path.exists(loc):
			os.mkdir(loc)
		IDs.write(loc+'targetIDs.txt',format='csv',delimiter='\t',overwrite=True)

	return IDs


def get_xrt(GRB,uselocal=True,keep=False):
    """
	Retrieves the XRT 0.3 - 10keV flux light curves for a given GRB.

	Args:
		GRB (str): The name of the GRB, e.g. '060614'.
		uselocal (bool, optional): If True, checks for a locally saved version of the data file before attempting the download. Defaults to True.
		keep (bool, optional): If True, saves the data locally after use. Defaults to False.
	
	Returns:
		data (astropy.table.Table): Lightcuve data containing columns - 'time','tpos','tneg','flux','fpos','fneg'
	"""

	if uselocal == True:
		try:
			data = ascii.read(loc+GRB+'_xray_flux.txt')
			print('Local file found for '+GRB)
			return data
		except FileNotFoundError:
			pass

	base = 'https://www.swift.ac.uk/xrt_curves/'
	
	IDs = ascii.read(loc+'targetIDs.txt')
	#tID = str("{:08d}".format(IDs['targetID'][np.where(IDs['GRB'] == GRB)][0]))
	tIDs = np.unique(IDs['targetID'][np.where(IDs['GRB'] == GRB)])
	if len(tIDs) == 0:
		return -888.

	for tID in tIDs:
		url = base+str("{:08d}".format(tID))+'/flux.qdp'
		try:
			with urllib.request.urlopen(url) as f:
				string = f.read().decode('utf-8').splitlines()
		except HTTPError:
			string = -404.	# Webpage not found
			continue
		if string[0][0] == '<':
			string = -999.	# Webpage exists but data file does not.
			continue
		break	# If data is found for a target ID, end the loop.
	
	if string == -404. or string == -999.:
		return string
	
	Time = []
	Tpos = []
	Tneg = []
	Flux = []
	Fpos = []
	Fneg = []
	
	for line in string:
		if len(line.split()) == 6 and line.split()[0] != 'NO' and line.split()[0] != '!Time':
			Time = np.append(Time,float(line.split()[0]))
			Tpos = np.append(Tpos,float(line.split()[1]))
			Tneg = np.append(Tneg,np.sqrt(float(line.split()[2])**2.))
			Flux = np.append(Flux,float(line.split()[3]))
			Fpos = np.append(Fpos,float(line.split()[4]))
			Fneg = np.append(Fneg,np.sqrt(float(line.split()[5])**2.))
		
	data = Table([Time,Tpos,Tneg,Flux,Fpos,Fneg],names=('time','tpos','tneg','flux','fpos','fneg'))
	data.sort('time')
	
	if keep == True:
		if not os.path.exists(loc):
			os.mkdir(loc)
		# if not os.path.exists(loc+GRB+'/xray'):
		# 	os.mkdir(loc+GRB+'/xray')
		data.write(loc+GRB+'_xray_flux.txt',format='csv',delimiter='\t',overwrite=True)

	return data
	
	
def get_batxrt(GRB,snr='4',band='XRT',evolving=False,spec=False,uselocal=True,keep=False):
    
	
	if uselocal == True:
		try:
			if spec == True:
				data = ascii.read(loc+GRB+'/xray/spec.txt')
			else:
				data = ascii.read(loc+GRB+'/xray/batxrt.txt')
			print('Local file found for '+GRB)
			return data
		except FileNotFoundError:
			pass
	
	cwd = os.getcwd()	# Record the current working directory to return to later
	
	base = 'https://www.swift.ac.uk/burst_analyser/'	# Base of the UKSSDC url
	
	# Find the target ID for the desired GRB (required for the url and navigating the directories)
	IDs = ascii.read(loc+'targetIDs.txt')
	#tID = str("{:08d}".format(IDs['targetID'][np.where(IDs['GRB'] == GRB)][0]))
	tIDs = np.unique(IDs['targetID'][np.where(IDs['GRB'] == GRB)])
	
	# Create a temporary folder if none exists in the selected location.
	if not os.path.exists(loc+'temp'):
		os.mkdir(loc+'temp')
	
	for line in tIDs:
		url = base+str("{:08d}".format(line))+'/batxrtfiles_'+str("{:08d}".format(line))+'.tar'
		try:
			urllib.request.urlretrieve(url,loc+'temp/download.tar')
			tID = str("{:08d}".format(line))
		except HTTPError:
			tID = -404.	# Webpage not found
			continue	# Continue cycles the loop without triggering the 'break' clause.
		break	# If data is found for a target ID, end the loop.
	
	if tID == -404.:
		return tID
	
	#url = base+tID+'/batxrtfiles_'+tID+'.tar'

	# Download and unpack the data tarball	
	#try:
	#	urllib.request.urlretrieve(url,loc+'temp/download.tar')
	#except HTTPError:
	#	return -404.
	
	os.chdir(loc+'temp')
	stdout = os.system('tar -xf download.tar')
	
	# Fill in the filename gaps to get the requested file based on the optional keywords given.
	if evolving == False:
		batevolve = '_NOEVOLVE'
		xrtevolve = '_nosys'
	else:
		batevolve = ''
		xrtevolve = ''
	
	# Append BAT, WT and PC files to directory paths
	batfile = loc+'temp/'+tID+'/bat/bat_flux_snr'+snr+'_'+band+'BAND'+batevolve+'.qdp'
	wtfile = loc+'temp/'+tID+'/xrt/xrt_flux_wt_'+band+'BAND'+xrtevolve+'.qdp'
	pcfile = loc+'temp/'+tID+'/xrt/xrt_flux_pc_'+band+'BAND'+xrtevolve+'.qdp'
	
	if spec == True:
		batfile = loc+'temp/'+tID+'/bat/bat_gamma_snr'+snr+'_'+band+'BAND.qdp'
		wtfile = loc+'temp/'+tID+'/xrt/xrt_gamma_wt.qdp'
		pcfile = loc+'temp/'+tID+'/xrt/xrt_gamma_pc.qdp'
        
	Time = []
	Tpos = []
	Tneg = []
	Flux = []
	Fpos = []
	Fneg = []
	
	# Read elements from BAT file
	try:
		with open(batfile, 'r') as string:
			for line in string:
				if len(line.split()) == 6 and line.split()[0] != 'NO' and line.split()[0][0] != '!':
					Time = np.append(Time,float(line.split()[0]))
					Tpos = np.append(Tpos,float(line.split()[1]))
					Tneg = np.append(Tneg,np.sqrt(float(line.split()[2])**2.))
					Flux = np.append(Flux,float(line.split()[3]))
					Fpos = np.append(Fpos,float(line.split()[4]))
					Fneg = np.append(Fneg,np.sqrt(float(line.split()[5])**2.))
			if max(Flux) == 0.:
				print('WARNING: the maximum BAT flux in this file = 0. This can often be solved by re-running swift_scrape with the keyword evolving = True.')
	except FileNotFoundError:	# Pass if there is no BAT file
		print('No BAT file found for '+GRB)
	
	# Read elements from WT file			
	try:
		with open(wtfile, 'r') as string:
			for line in string:
				if len(line.split()) == 6 and line.split()[0] != 'NO' and line.split()[0][0] != '!':
					Time = np.append(Time,float(line.split()[0]))
					Tpos = np.append(Tpos,float(line.split()[1]))
					Tneg = np.append(Tneg,np.sqrt(float(line.split()[2])**2.))
					Flux = np.append(Flux,float(line.split()[3]))
					Fpos = np.append(Fpos,float(line.split()[4]))
					Fneg = np.append(Fneg,np.sqrt(float(line.split()[5])**2.))
	except FileNotFoundError:	# Pass if there is no WT file
		print('No WT file found for '+GRB)
	
	# Read elements from PC file			
	try:
		with open(pcfile, 'r') as string:
			for line in string:
				if len(line.split()) == 6 and line.split()[0] != 'NO' and line.split()[0][0] != '!':
					Time = np.append(Time,float(line.split()[0]))
					Tpos = np.append(Tpos,float(line.split()[1]))
					Tneg = np.append(Tneg,np.sqrt(float(line.split()[2])**2.))
					Flux = np.append(Flux,float(line.split()[3]))
					Fpos = np.append(Fpos,float(line.split()[4]))
					Fneg = np.append(Fneg,np.sqrt(float(line.split()[5])**2.))
	except FileNotFoundError:	# Pass if there is no PC file
		print('No PC file found for '+GRB)
	
	# Organise in an astropy table and sort by time.
	if spec == True:
		data = Table([Time,Tpos,Tneg,Flux,Fpos/1.645,Fneg/1.645],names=('time','tpos','tneg','gamma','gpos','gneg'))
	else:
		data = Table([Time,Tpos,Tneg,Flux,Fpos,Fneg],names=('time','tpos','tneg','flux','fpos','fneg'))
	data.sort('time')
	if not os.path.exists(loc+GRB):
			os.mkdir(loc+GRB)
	if not os.path.exists(loc+GRB+'/xray'):
			os.mkdir(loc+GRB+'/xray')
	if spec == True:
		data.write(loc+GRB+'/xray/spec.txt',format='csv',delimiter='\t',overwrite=True)
	else:
		data.write(loc+GRB+'/xray/batxrt.txt',format='csv',delimiter='\t',overwrite=True)
	
	# Option to save the whole download.
	if keep == True:
		try:
			os.rename(loc+'temp/'+tID, loc+GRB+'/'+tID)
		except OSError:
			print(tID+' directory already exists for GRB '+GRB+'. This was not overwritten.')
	
	# Remove temporary directory
	os.chdir(loc)
	stdout = os.system('rm -Rf temp')
	
	# Go back to initial working directory
	os.chdir(cwd)
	
	return data
	

def get_xrtdense(GRB,uselocal=True,keep=False):
    """
    Retrieves the 1keV BAT+XRT flux density light curves from the UKSSDC (in Jy). SNR = 4, no spectral evolution.
    
	Args:
		GRB (str): The name of the GRB, e.g. '060614'.
		uselocal (bool, optional): If True, checks for a locally saved version of the data file before attempting the download. Defaults to True.
		keep (bool, optional): If True, saves the data locally after use. Defaults to False.

	Returns:
		data (astropy.table.Table): Lightcuve data containing columns - 'time','tpos','tneg','flux','fpos','fneg'
	"""
	
	if uselocal == True:
		try:
			data = ascii.read(loc+GRB+'/xray/flux_density.txt')
			return data
		except FileNotFoundError:
			print('No local file found for '+GRB+'. Downloading from the UKSSDC.')
	
	cwd = os.getcwd()	# Record the current working directory to return to later
	
	base = 'https://www.swift.ac.uk/burst_analyser/'	# Base of the UKSSDC url
	
	# Find the target ID for the desired GRB (required for the url and navigating the directories)
	IDs = ascii.read(loc+'targetIDs.txt')
	tID = str("{:08d}".format(IDs['targetID'][np.where(IDs['GRB'] == GRB)][0]))
	
	url = base+tID+'/batxrtfiles_'+tID+'.tar'
	
	# Create a temporary folder if none exists in the selected location.
	if not os.path.exists(loc+'temp'):
		os.mkdir(loc+'temp')
	
	# Download and unpack the data tarball	
	urllib.request.urlretrieve(url,loc+'temp/download.tar')
	os.chdir(loc+'temp')
	stdout = os.system('tar -xf download.tar')

	# Append WT and PC files to directory paths
	wtfile = loc+'temp/'+tID+'/xrt/xrt_flux_wt_OBSDENSITY_nosys.qdp'
	pcfile = loc+'temp/'+tID+'/xrt/xrt_flux_pc_OBSDENSITY_nosys.qdp'
        
	Time = []
	Tpos = []
	Tneg = []
	Flux = []
	Fpos = []
	Fneg = []
	
	# Read elements from WT file			
	try:
		with open(wtfile, 'r') as string:
			for line in string:
				if len(line.split()) == 6 and line.split()[0] != 'NO' and line.split()[0][0] != '!':
					Time = np.append(Time,float(line.split()[0]))
					Tpos = np.append(Tpos,float(line.split()[1]))
					Tneg = np.append(Tneg,np.sqrt(float(line.split()[2])**2.))
					Flux = np.append(Flux,float(line.split()[3]))
					Fpos = np.append(Fpos,float(line.split()[4]))
					Fneg = np.append(Fneg,np.sqrt(float(line.split()[5])**2.))
	except FileNotFoundError:	# Pass if there is no WT file
		print('No WT file found for '+GRB)
	
	# Read elements from PC file			
	try:
		with open(pcfile, 'r') as string:
			for line in string:
				if len(line.split()) == 6 and line.split()[0] != 'NO' and line.split()[0][0] != '!':
					Time = np.append(Time,float(line.split()[0]))
					Tpos = np.append(Tpos,float(line.split()[1]))
					Tneg = np.append(Tneg,np.sqrt(float(line.split()[2])**2.))
					Flux = np.append(Flux,float(line.split()[3]))
					Fpos = np.append(Fpos,float(line.split()[4]))
					Fneg = np.append(Fneg,np.sqrt(float(line.split()[5])**2.))
	except FileNotFoundError:	# Pass if there is no PC file
		print('No PC file found for '+GRB)
	
	# Organise in an astropy table and sort by time.
	data = Table([Time,Tpos,Tneg,Flux,Fpos,Fneg],names=('time','tpos','tneg','flux','fpos','fneg'))
	data.sort('time')

	# Option to save the flux density file.
	if keep == True:
		if not os.path.exists(loc+GRB):
			os.mkdir(loc+GRB)
		if not os.path.exists(loc+GRB+'/xray'):
			os.mkdir(loc+GRB+'/xray')
		data.write(loc+GRB+'/xray/flux_density.txt',format='csv',delimiter='\t',overwrite=True)
	
	# Remove temporary directory
	os.chdir(loc)
	stdout = os.system('rm -Rf temp')
	
	# Go back to initial working directory	
	os.chdir(cwd)
	
	return data
	
	
def t90(GRB):
	
	base = "https://gcn.gsfc.nasa.gov/notices_s/"
	IDs = ascii.read(loc+'targetIDs.txt')
	
	#tID = str("{:06d}".format(IDs['targetID'][np.where(IDs['GRB'] == GRB)][0]))
	tIDs = np.unique(IDs['targetID'][np.where(IDs['GRB'] == GRB)])

	for line in tIDs:
		url = base+str("{:06d}".format(line))+'/BA/'
		try:
			with urllib.request.urlopen(url) as f:
				string = f.read().decode('utf-8').splitlines()
			tID = str("{:06d}".format(line))
		except HTTPError:
			tID = -404., -404.	# Webpage not found
			continue	# Continue cycles the loop without triggering the 'break' clause.
		break	# If data is found for a target ID, end the loop.
	
	if tID[0] == -404.:
		return tID

	#url = base+tID+'/BA/'
	#try:
	#	with urllib.request.urlopen(url) as f:
	#		string = f.read().decode('utf-8').splitlines()
	#except HTTPError:
	#	return -404., -404.	# Webpage not found.
	
	for i in range(0,len(string)):
		try:
			if string[i].split()[0] == 'T90:':
				return 	np.round(float(string[i].split()[1]),3), np.round(float(string[i].split()[3]),3)	# Return T90 and error.
		except IndexError:
			pass
    
	return -999., -999.	# T90 not found.
	
	
def find_pho(GRB):	# Scrapes the UKSSDC automatic spectrum fits and returns the last value of photon index (intended to be the late-time photon counting mode fit).

	IDs = ascii.read(loc+'targetIDs.txt')
	tIDs = np.unique(IDs['targetID'][np.where(IDs['GRB'] == GRB)])
	base = 'https://www.swift.ac.uk/xrt_spectra/'
	
	for tID in tIDs:
		url = base+str("{:08d}".format(tID))+'/'
		try:
			with urllib.request.urlopen(url) as f:
				string = f.read().decode('utf-8').splitlines()
		except HTTPError:
			string = -404.	# Webpage not found
			continue
		break	# If data is found for a target ID, end the loop.
	
	if string == -404. or string == -999.:
		return float(string), float(string), float(string)
		
	for i, line in enumerate(string):
		if 'Photon index' in line:
			j = i
	
	try:
		pho, phopos, phoneg = string[j][37:-11].split()
		phopos = float(phopos[2:-1])
		phoneg = float(phoneg[1:])
	except UnboundLocalError:
		return -404.,-404.,-404.

	return float(pho), phopos, phoneg

