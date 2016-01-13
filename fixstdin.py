#-*- encoding: utf-8 -*-
import sys
import codecs
stdin = sys.stdin.detach()
#stdout = sys.stdout.detach()
sys.stdin = codecs.getreader('utf-8')(stdin,errors='replace')
sys.stdin.encoding = 'utf-8'
#sys.stdout = codecs.getwriter('utf-8')(stdout)
print("Fixed unicode é")
