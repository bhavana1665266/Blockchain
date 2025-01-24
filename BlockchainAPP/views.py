from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages
from django.http import HttpResponse
from Blockchain import *
from Block import *
import datetime
import pyaes, pbkdf2, binascii, os, secrets
import base64
import ipfsApi
import os
from django.core.files.storage import FileSystemStorage
import pickle

api = ipfsApi.Client(host='http://127.0.0.1', port=5001)

blockchain = Blockchain()
if os.path.exists('blockchain_contract.txt'):
    with open('blockchain_contract.txt', 'rb') as fileinput:
        blockchain = pickle.load(fileinput)
    fileinput.close()

def getKey(): #generating key with PBKDF2 for AES
    password = "s3cr3t*c0d3"
    passwordSalt = '76895'
    key = pbkdf2.PBKDF2(password, passwordSalt).read(32)
    return key

def encrypt(plaintext): #AES data encryption
    aes = pyaes.AESModeOfOperationCTR(getKey(), pyaes.Counter(31129547035000047302952433967654195398124239844566322884172163637846056248223))
    ciphertext = aes.encrypt(plaintext)
    return ciphertext

def decrypt(enc): #AES data decryption
    aes = pyaes.AESModeOfOperationCTR(getKey(), pyaes.Counter(31129547035000047302952433967654195398124239844566322884172163637846056248223))
    decrypted = aes.decrypt(enc)
    return decrypted

def index(request):
    if request.method == 'GET':
       return render(request, 'index.html', {})

def Login(request):
    if request.method == 'GET':
       return render(request, 'Login.html', {})

def Signup(request):
    if request.method == 'GET':
       return render(request, 'Signup.html', {})

def PublishTweets(request):
    if request.method == 'GET':
       return render(request, 'PublishTweets.html', {})

def ViewTweets(request):
    #data = "post#"+user+"#"+post_message+"#"+str(hashcode)+"#"+str(current_time)
    if request.method == 'GET':
        strdata = '<table border=1 align=center width=100%><tr><th><font size='' color=black>Tweet Owner</th><th><font size='' color=black>Tweet Message</th>'
        strdata+='<th><font size='' color=black>IPFS Image Hashcode</th><th><font size='' color=black>Tweet Image</th>'
        strdata+='<th><font size='' color=black>Tweet Date Time</th></tr>'
        for root, dirs, directory in os.walk('static/tweetimages'):
            for j in range(len(directory)):
                os.remove('static/tweetimages/'+directory[j])
        for i in range(len(blockchain.chain)):
            if i > 0:
                b = blockchain.chain[i]
                data = b.transactions[0]
                data = base64.b64decode(data)
                data = str(decrypt(data))
                data = data[2:len(data)-1]
                print(data)
                row = data.split("#")
                if row[0] == "post":
                    print(row[3])
                    content = api.get_pyobj(row[3])
                    content = pickle.loads(content)
                    with open("C:BlockchainAPP/static/tweetimages"+row[5], "wb") as file:
                        file.write(content)
                    file.close()
                    strdata+='<tr><td><font size='' color=black>'+str(row[1])+'</td><td><font size='' color=black>'+row[2]+'</td><td><font size='' color=black>'+str(row[3])+'</td>'
                    strdata+='<td><img src=static/tweetimages/'+row[5]+'  width=200 height=200></img></td>'
                    strdata+='<td><font size='' color=black>'+str(row[4])+'</td>'
        context= {'data':strdata}
        return render(request, 'ViewTweets.html', context)    

def LoginAction(request):
    if request.method == 'POST':
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        utype='none'
        for i in range(len(blockchain.chain)):
            if i > 0:
                b = blockchain.chain[i]
                data = b.transactions[0]
                data = base64.b64decode(data)
                data = str(decrypt(data))
                data = data[2:len(data)-1]
                print(data)
                arr = data.split("#")
                if arr[0] == "signup":
                    if arr[1] == username and arr[2] == password:
                        utype = username
                        break
        if utype != 'none':
            file = open('session.txt','w')
            file.write(utype)
            file.close()   
            context= {'data':'welcome '+username}
            return render(request, 'UserScreen.html', context)
        else:
            context= {'data':'login failed'}
            return render(request, 'Login.html', context)

def isUserExist(username):
    flag = False
    for i in range(len(blockchain.chain)):
        if i > 0:
            b = blockchain.chain[i]
            data = b.transactions[0]
            data = base64.b64decode(data)
            data = str(decrypt(data))
            data = data[2:len(data)-1]
            arr = data.split("#")
            if arr[0] == "signup":
                if arr[1] == username:
                    flag = True
                    break
    return flag                

        
def PublishTweetsAction(request):
    if request.method == 'POST':
        post_message = request.POST.get('t1', False)
        filename = request.FILES['t2'].name
        myfile = request.FILES['t2'].read()
        myfile = pickle.dumps(myfile)
        now = datetime.datetime.now()
        current_time = now.strftime("%Y-%m-%d %H:%M:%S")
        user = ''
        with open("session.txt", "r") as file:
            for line in file:
                user = line.strip('\n')
        file.close()
        hashcode = api.add_pyobj(myfile)
        data = "post#"+user+"#"+post_message+"#"+str(hashcode)+"#"+str(current_time)+"#"+filename
        enc = encrypt(str(data))
        output = "Error in storing data in Blockchain"
        enc = str(base64.b64encode(enc),'utf-8')
        blockchain.add_new_transaction(enc)
        hash = blockchain.mine()
        b = blockchain.chain[len(blockchain.chain)-1]
        print("Encrypted Data : "+str(b.transactions[0])+" Previous Hash : "+str(b.previous_hash)+" Block No : "+str(b.index)+" Current Hash : "+str(b.hash))
        bc = "Encrypted Data : "+str(b.transactions[0])+" Previous Hash : "+str(b.previous_hash)+"<br/>Block No : "+str(b.index)+"<br/>Current Hash : "+str(b.hash)
        blockchain.save_object(blockchain,'blockchain_contract.txt')
        output = 'Tweet saved in Blockchain with below hashcodes & Media file saved in IPFS.<br/>'+bc
        context= {'data':output}
        if os.path.exists(filename) == True:
            os.remove(filename)
        return render(request, 'PublishTweets.html', context)
        

def SignupAction(request):
    if request.method == 'POST':
        username = request.POST.get('t1', False)
        password = request.POST.get('t2', False)
        contact = request.POST.get('t3', False)
        gender = request.POST.get('t4', False)
        email = request.POST.get('t5', False)
        address = request.POST.get('t6', False)
        output = "Username already exists"
        if isUserExist(username) == False:
            data = "signup#"+username+"#"+password+"#"+contact+"#"+gender+"#"+email+"#"+address
            enc = encrypt(str(data))
            enc = str(base64.b64encode(enc),'utf-8')
            blockchain.add_new_transaction(enc)
            hash = blockchain.mine()
            b = blockchain.chain[len(blockchain.chain)-1]
            print("Encrypted Data : "+str(b.transactions[0])+" Previous Hash : "+str(b.previous_hash)+" Block No : "+str(b.index)+" Current Hash : "+str(b.hash))
            bc = "Encrypted Data : "+str(b.transactions[0])+" Previous Hash : "+str(b.previous_hash)+"<br/>Block No : "+str(b.index)+"<br/>Current Hash : "+str(b.hash)
            blockchain.save_object(blockchain,'blockchain_contract.txt')
            output = 'Signup process completd and record saved in Blockchain with below hashcodes.<br/>'+bc
        context= {'data':output}
        return render(request, 'Signup.html', context)
    







