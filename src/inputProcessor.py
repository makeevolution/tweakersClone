import sys, getopt

def getSearchTermFromInput():
        try:
            argv = sys.argv[1:]
        except IndexError:
            sys.exit("Use -h for more help")

        try:
            opts, searchTerm = getopt.getopt(argv, "ho:", ["help", "output-file="])
        except getopt.GetoptError as err:
            print(err)
            sys.exit(2)
        
        if not searchTerm:
            if "-h" not in str(opts) or "-help" not in str(opts):
                print("Error: At least one search term must be included!")
                sys.exit(__doc__)

        searchTerm = " ".join(searchTerm)
        outputFile = []
        for opt, arg in opts:
            if opt in ["-h","--help"]:
                sys.exit(__doc__)
            elif opt in ["-o","--output-file"]:
                if ".json" in arg:
                    outputFile = arg.strip()
                else:
                    print("Error: Write to specified file type is not possible!")
                    sys.exit(__doc__)
            else:
                print("Error: option {} not available".format(opt))
                sys.exit(__doc__)

        return searchTerm
