import os,sys
term = os.environ.get('TERM')
if term == 'screen':
    def set(title):
        sys.stdout.write("\033_"+title+"\a\\")
        sys.stdout.flush()
else:
    def set(title):
        sys.stdout.write("\033]0;"+title+"\a")
        sys.stdout.flush()

if __name__ == '__main__':
    set('test')
    input()
