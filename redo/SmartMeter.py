import sys

class SmartMeter:
    def __init__(self,id):
        self.ID= id







def main():
    ID= sys.argv[1]
    sm = SmartMeter(ID)




if __name__ == '__main__':
    main()