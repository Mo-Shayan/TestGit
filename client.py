import socket
import threading
import re
from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd,messagebox
from PIL import ImageTk, Image
from datetime import datetime
import math
import os
import time
#Send messages to server
images=[]
frames=[]
def send(msg,count):
    #Check if Server and client are connected before trying to send a message
    try:
        if(len(msg)!=0):    #If message is empty
            formatted_msg=f"{datetime.now().strftime('%H:%M')}\n\t{name.get()}\n\t{msg}"
            client.send(formatted_msg.encode())
            user_time,user_name,user_data=formatted_msg.split('\n\t')
            frames.append(Frame(textFrame,bg="#00d2ff"))
            frames[-1].grid(column=1,row=count[0],sticky=E,pady=2)
            ttk.Label(frames[-1],text=user_time,background='#00d2ff').grid(row=0,column=0,sticky=E)
            ttk.Label(frames[-1],text=user_name+':',background='#00d2ff',font=('Helvetica bold',12)).grid(row=1,column=0,sticky=W)     #Print message on GUI
            ttk.Label(frames[-1],text=user_data,background='#00d2ff',font=('Helvetica',15)).grid(row=1,column=1,sticky=W)
            count[0]+=1
            msgInput.delete(0,END)                                  #Clear the input bar on GUI
    except Exception as ex:
        print(ex)
        connectionStatus.set("Disconnected")                        #Server and client disconnected
    return

#Receive messages from server
def receive(addr,count):
    print(addr)
    ip,port=addr            #Ip and Port of Server
    typing_msg=StringVar()
    typing=Label(textFrame,textvariable=typing_msg)
    while True:
        msg=client.recv(2048).decode()
        print(msg,'from user')
        if not msg:                     #If Server Disconnects
            break
        if msg[-6:]=="TYPING":
            typing_msg.set(msg)
            typing.grid(column=0,row=count[0],sticky=W,pady=2)
            continue
        if msg=='sending video':
            temp=client.recv(1024).decode()
            extension,size,sender_name=temp.split('\n')
            file=open(f"{name.get()}{count[0]+1}{extension}",'wb')
            fileBytes=b""
            done=False
            percent=StringVar()
            download_status=Label(textFrame,textvariable=percent)
            download_status.grid(column=0,row=count[0],sticky=W)
            while not done:
                data=client.recv(2048)
                fileBytes+=data
                current_percent=math.floor((len(fileBytes)/int(size))*100)
                print(current_percent,' percent completed')
                percent.set(f"{current_percent} % Downloaded")
                if fileBytes[-5:]==b"<END>":
                    done=True
            file.write(fileBytes)
            filename=file.name
            file.close()
            download_status.grid_forget()
            if extension in ['.mp4','.mkv']:
                Button(textFrame,background='#FEE134',text=f"{sender_name} sent a video",command=lambda: os.startfile(filename),pady=2).grid(column=0,row=count[0],sticky=W)
                count[0]+=1
            elif extension in ['.txt','.pdf','.docx','.mp3','.csv','.ppt','.xlsx']:
                Button(textFrame,background='#FEE134',text=f"{sender_name} sent a document",command=lambda: os.startfile(filename),pady=2).grid(column=0,row=count[0],sticky=W)
                count[0]+=1
            continue
        if msg=='sending image':
            temp=client.recv(1024).decode()
            print(temp)
            extension,size,sender_name=temp.split('\n')
            file=open(f"{name.get()}{count[0]+1}{extension}",'wb')
            fileBytes=b""
            done=False
            while not done:
                data=client.recv(2048)
                fileBytes+=data
                if fileBytes[-5:]==b"<END>":
                    done=True
            file.write(fileBytes)
            filename=file.name
            file.close()
            img=Image.open(filename)
            resized_image= img.resize((150,150), Image.ANTIALIAS)
            images.append(ImageTk.PhotoImage(resized_image))
            print('here')
            Label(textFrame,image=images[-1],width=150,height=150,background='#FEE134').grid(column=0,row=count[0],sticky=W)
            count[0]+=1
            Label(textFrame,text=f'{sender_name}').grid(column=0,row=count[0],sticky=W)
            count[0]+=1
            continue
        typing.grid_forget()
        user_time,user_name,user_data=msg.split('\n\t')
        frames.append(Frame(textFrame,bg="#FEE134"))
        frames[-1].grid(column=0,row=count[0],sticky=W,pady=2)
        ttk.Label(frames[-1],text=user_time,background='#FEE134').grid(row=0,column=0,sticky=W,columnspan=2)
        ttk.Label(frames[-1],text=user_name+':',background='#FEE134',font=('Helvetica bold',12)).grid(row=1,column=0,sticky=E)     #Print message on GUI
        ttk.Label(frames[-1],text=user_data,background='#FEE134',font=('Helvetica',15)).grid(row=1,column=1,sticky=E)
        print(f"{user_name}: {user_data}")
        count[0]+=1
        if(msg=='diss'):                #If Server Disconnects
            break
    client.close()
    return
def main(count):
    addr=('192.168.56.1',3000)
    global client
    client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        client.connect(addr)
        client.send(f'NAME\n{name.get()}'.encode())
        msg=client.recv(1024).decode()
        print('msg on 79',msg)
        if msg=='RENAME':
            endConnection()
            message.set("Duplicate username, choose another one")
            return
        else:
            message.set("Username Available")
            ttk.Button(loginFrame,text="Group Chat",command=lambda:chatScreen(addr)).grid(row=0,column=4)
            ttk.Button(loginFrame,text="Private Chat",command= lambda:listening(addr)).grid(row=0,column=3)
            if msg=='Noone online':
                Label(loginFrame,text="No one Currently Online").grid(row=2,column=0)
                return
            active_users=msg.split('\n')
            active_users.pop()
            Label(loginFrame,text="List of Online People: ").grid(row=2,column=0)
            i=3
            for user in active_users:
                Label(loginFrame,text=str(user)).grid(row=i,column=0)
                ttk.Button(loginFrame,text="Private Chat",command=lambda:chatScreen(addr,user)).grid(row=i,column=1)
                i+=1
    except Exception as e:
        print(e)
        connectionStatus.set("No Port open on the specified Ip Address and Port")
    return
def listening(addr):
    client.send(b"PRIVATE")
    notification_thread=threading.Thread(target=notifications,args=(addr,))
    notification_thread.start()
def start(count):
    print("in main")
    mainThread=threading.Thread(target=main,args=(count,))       #New Thread to deal with client-Server communication
    mainThread.start()
    return
def notifications(addr):
    msg=client.recv(2048).decode()
    print('pribae',msg)
    Label(loginFrame,text=f"{msg} wants to private chat: ").grid(row=5,column=0)
    ttk.Button(loginFrame,text="Start Private Chat",command= lambda: chatScreen(addr,msg,"ACCEPT")).grid(column=1,row=5)
    return
def endConnection():
    try:
        client.send("diss".encode())
        connectionStatus.set("Disconnected")
    except:
        pass
    return
def close():
    endConnection()
    root.destroy()      #Close Window

def openFile(count):
    file=fd.askopenfile(mode='rb')
    if file is not None:
        client.send('sending image'.encode())
        size=os.path.getsize(file.name)
        _,extension=os.path.splitext(file.name)
        print(size)
        client.send(f"{extension}\n{size}\n{name.get()}".encode())
        time.sleep(1)
        data=file.read()
        client.sendall(data)
        client.send(b"<END>")
        filename=file.name
        file.close()
        if extension in ['.mp4','.mkv']:
            Button(textFrame,background='#00d2ff',text=f"You sent a video",command=lambda: os.startfile(filename),pady=2).grid(column=1,row=count[0],sticky=E)
            count[0]+=1
            return
        elif extension in ['.txt','.pdf','.docx','.mp3','.csv','.ppt','.xlsx']:
            Button(textFrame,background='#FEE134',text=f"You sent a document",command=lambda: os.startfile(filename),pady=2).grid(column=1,row=count[0],sticky=E)
            count[0]+=1
            return
        img=Image.open(filename)
        resized_image= img.resize((150,150), Image.ANTIALIAS)
        images.append(ImageTk.PhotoImage(resized_image))
        Label(textFrame,image=images[-1],width=150,height=150,background='#00d2ff').grid(column=1,row=count[0],sticky=E)
        count[0]+=1
        Label(textFrame,text=f'{name.get()}').grid(column=0,row=count[0],sticky=E)
        count[0]+=1
def group_chat(addr):
    client.send("GROUP".encode())
    connectionStatus.set("Connected")
    group_chat_thread=threading.Thread(target=receive,args=(addr,count))       #New Thread to deal with client-Server communication
    group_chat_thread.start()
def private_chat(user,addr,req):
    client.send(f'{req}\n{user}'.encode())
    connectionStatus.set("Connected")
    private_chat_thread=threading.Thread(target=receive,args=(addr,count))
    private_chat_thread.start()
def back():
    mainframe.grid_forget()
    loginFrame.grid(row=0,column=0,sticky=(N, W, E, S))

root=Tk()
global connectionStatus
connectionStatus=StringVar()
connectionStatus.set("Disconnected")
root.title("E-CHAT")
root.geometry("700x500")
Label(root,text="Welcome to E-Chat").grid(column=0,row=0)
loginFrame=Frame(root)
loginFrame.grid(column=0,row=1)
ttk.Label(loginFrame,text="Enter Name: ").grid(row=0,column=0)
name=StringVar()
message=StringVar()
message.set('X')
Label(loginFrame,textvariable=message).grid(column=0,row=1)
name_input=ttk.Entry(loginFrame,width=30,textvariable=name)
name_input.grid(row=0,column=1)
name_input.bind("<Return>",lambda event:start(count))
btn=ttk.Button(loginFrame,text="Enter",command=lambda: start(count)).grid(row=0,column=2)
count=[1]
def typing_status(event):
    client.send(f"{name.get()} is TYPING".encode())
def chatScreen(addr,user=None,req="REQUEST"):
    loginFrame.grid_forget()
    global mainframe
    mainframe=ttk.Frame(root,padding="3 3 12 12")
    mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    global msgInput;global textFrame
    ttk.Label(mainframe,textvariable=connectionStatus).grid(column=0,row=0)
    canvas=Canvas(mainframe,width=500,height=400)
    canvas.columnconfigure(0,weight=2)
    scrollbar = ttk.Scrollbar(mainframe, orient="vertical", command=canvas.yview)
    textFrame=Frame(canvas,width=500,height=400)
    # Label(textFrame,text="Welcom to chatroom",width=70,background="#00d2ff").grid(row=0,column=0,sticky='EW')
    if user==None:
        group_chat(addr)
    else:
        private_chat(user,addr,req)
    textFrame.bind("<Configure>",lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((1, 1), window=textFrame,anchor='nw')
    canvas.grid(row=1,column=0)
    scrollbar.grid(row=1,column=1)
    msg=StringVar()
    ttk.Label(mainframe,text="Enter your message:  ").grid(column=0,row=2)
    msgInput=ttk.Entry(mainframe,width=50,textvariable=msg)
    msgInput.grid(row=3,column=0)
    msgInput.bind("<Return>",lambda event:send(msg.get(),count))
    msgInput.bind("<Key>",typing_status)
    ttk.Button(mainframe,text="Send",command=lambda:send(msg.get(),count)).grid(column=1,row=3)
    ttk.Button(mainframe,text="Close",command=close).grid(column=0,row=4)
    ttk.Button(mainframe,text="Disconnect",command=endConnection).grid(column=1,row=4)
    ttk.Button(mainframe,text="Open",command=lambda: openFile(count)).grid(column=2,row=3)
    ttk.Button(mainframe,text="Back",command=lambda:back()).grid(column=2,row=4)
root.protocol("WM_DELETE_WINDOW", close)
root.mainloop()
