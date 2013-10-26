#-------------------------
# Main
#-------------------------

from shots import Shot

import sys

def main():
	debugging = False
	
	if len(sys.argv) < 2:
		exit("Usage : " + sys.argv[0] + " <filename> [-d]\n        " + sys.argv[0] + " requires at least a file name as a parameter, with an optional debug flag")
	elif len(sys.argv) > 2:
		if sys.argv[2] == "-d":
			debugging = True

	fileName = sys.argv[1]

	s = Shot(fileName,debug=debugging)
	print s.generateCode()

if __name__ == "__main__":
	main()
