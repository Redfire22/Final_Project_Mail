import sqlite3
import smtplib
import imaplib
import email
from datetime import datetime
import time
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup

DOMAIN = 'imap.gmail.com'
EMAIL_ACCOUNT = "AAABBBNetwork@gmail.com"
PASSWORD = "NetworkArchi"


def cls():
    os.system('cls' if os.name == 'nt' else 'clear')


# Connect itself to the server mail, and do the following :
#   - Check if the user is registered in the database, if not, add him to it.
#   - Request all the mail, and check if they exist in the database, if not, add them.
def load_email():
    mail = imaplib.IMAP4_SSL(DOMAIN)
    mail.login(EMAIL_ACCOUNT, PASSWORD)
    mail.list()
    mail.select('INBOX')
    result, data = mail.uid('search', None, "ALL")
    i = len(data[0].split())

    conn = sqlite3.connect('database.db')

    c = conn.cursor()

    c.execute("SELECT count(*) FROM user WHERE mailaccount =?;", (EMAIL_ACCOUNT,))

    exist = c.fetchone()

    if exist[0] == 0:
        c.execute("INSERT INTO user(mailaccount,password) VALUES (?,?);", (EMAIL_ACCOUNT, PASSWORD))

    conn.commit()

    conn.close()

    for x in range(i):
        email_uid = data[0].split()[x]
        result, email_data = mail.uid('fetch', email_uid, '(RFC822)')
        # result, email_data = conn.store(num,'-FLAGS','\\Seen')
        # this might work to set flag to seen, if it doesn't already
        raw_email = email_data[0][1]
        raw_email_string = raw_email.decode('utf-8')
        email_message = email.message_from_string(raw_email_string)

        # Header Details
        date_tuple = email.utils.parsedate_tz(email_message['Date'])
        if date_tuple:
            local_date = datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
            local_message_date = "%s" % (str(local_date.strftime("%a, %d %b %Y %H:%M:%S")))
        email_from = str(email.header.make_header(email.header.decode_header(email_message['From'])))
        email_to = str(email.header.make_header(email.header.decode_header(email_message['To'])))
        subject = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))

        # Body details
        for part in email_message.walk():
            if part.get_content_type() == "text/plain":
                body = part.get_payload(decode=True)
            else:
                continue

        conn = sqlite3.connect('database.db')

        c = conn.cursor()

        c.execute("SELECT count(*) FROM email WHERE subject = ? AND toUser = ? AND date = ?",
                  (subject, email_to, local_message_date))

        exist = c.fetchone()

        if exist[0] == 0:
            c.execute(
                "INSERT INTO email(fromUser,toUser,date,subject,body, mailaccount) VALUES (?,?,?,?,?,?);",
                (email_from, email_to, local_message_date, subject, body.decode('utf-8'), EMAIL_ACCOUNT))

        conn.commit()

        conn.close()

    mail.close()
    mail.logout()


# Create the database, only if the database does not already exist
def set_database():
    conn = sqlite3.connect('database.db')

    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS user 
                        (mailaccount TEXT PRIMARY KEY,
                        password TEXT NOT NULL);''')

    c.execute('''CREATE TABLE IF NOT EXISTS email 
                    (id INTEGER PRIMARY KEY, 
                    fromUser TEXT NOT NULL, 
                    toUser TEXT NOT NULL, 
                    date TEXT NOT NULL, 
                    subject TEXT NOT NULL, 
                    body TEXT NOT NULL,
                    mailaccount TEXT,
                    FOREIGN KEY (mailaccount) REFERENCES user(id));''')

    conn.commit()

    conn.close()


# Self explanatory
def clean_table(delete_email, delete_user):
    conn = sqlite3.connect('database.db')

    c = conn.cursor()

    if delete_email:
        c.execute("DELETE FROM email WHERE 1=1")

    if delete_user:
        c.execute("DELETE FROM user WHERE 1=1")

    conn.commit()

    conn.close()


def order_mail_asc(order):
    conn = sqlite3.connect('database.db')

    c = conn.cursor()

    if order == "date":
        c.execute("SELECT * FROM email ORDER BY substr(date,0,4) || substr(date,5,7) || substr(date,8,10) ASC")
    else:
        c.execute("SELECT * FROM email ORDER BY ? ASC;", (order,))

    rows = c.fetchall()

    for row in rows:
        print(row)

    conn.commit()

    conn.close()


def order_mail_desc(order):
    conn = sqlite3.connect('database.db')

    c = conn.cursor()

    if order == "date":
        c.execute("SELECT * FROM email ORDER BY substr(date,0,4) || substr(date,5,7) || substr(date,8,10) DESC")
    else:
        c.execute("SELECT * FROM email ORDER BY ? DESC;", (order,))

    rows = c.fetchall()

    for row in rows:
        print(row)

    conn.commit()

    conn.close()


def display_mail():
    conn = sqlite3.connect('database.db')

    c = conn.cursor()

    c.execute("SELECT * FROM email;")

    rows = c.fetchall()

    for row in rows:
        print(str(row[0]) + ": from " + str(row[1]) + ", subject = "+str(row[4]))

    conn.commit()

    conn.close()


def display_mail_detail(id):
    conn = sqlite3.connect('database.db')

    c = conn.cursor()

    c.execute("SELECT * FROM email WHERE id = ?;", id)

    row = c.fetchone()

    print("FROM    : " + str(row[1]))

    print("TO      : " + str(row[2]))

    print("DATE    : " + str(row[3]))

    print("SUBJECT : " + str(row[4]))

    print("BODY : \n" + str(row[5]))

    conn.commit()

    conn.close()


def save_in_file(id):
    conn = sqlite3.connect('database.db')

    c = conn.cursor()

    c.execute("SELECT * FROM email WHERE id = ?;", id)

    row = c.fetchone()

    with open(str(row[1]) + "_" + str(row[4]) +"_" + str(row[3][0:11]) + ".txt", "w") as file:

        file.write("Email Save : " + str(row[1]) + "_" + str(row[4]) +"_" + str(row[3]) + ".txt\n\n")

        file.write("FROM    : " + str(row[1]) + "\n")

        file.write("TO      : " + str(row[2]) + "\n")

        file.write("DATE    : " + str(row[3]) + "\n")

        file.write("SUBJECT : " + str(row[4]) + "\n")

        file.write("BODY : \n" + str(row[5]))

    file.close()

    conn.commit()

    conn.close()


def send_email(email_from, email_to, subject, message, email_address, password):

    s = smtplib.SMTP('smtp.gmail.com', 587)

    s.starttls()

    s.login(email_address, password)

    msg = MIMEMultipart()

    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = subject

    body = message

    msg.attach(MIMEText(body, 'text'))

    s.send_message(msg)

    s.quit()


if __name__ == "__main__":

    print("Network Architecture Project : Mail client")
    print("By Clement RAMOND & Marc REYNAUD IOS-3")
    time.sleep(1)
    domain_kind = input("What kind of mail server ot you use ?\n  1 - Gmail" + "\n")
    if domain_kind == "1":
        DOMAIN = 'imap.gmail.com'
    else:
        temp = 1
        #TODO s'occuper d'autres plates-formes de mail ?


    email_address = input("Insert email address :" + "\n")
    if email_address == "a":
        EMAIL_ACCOUNT = "AAABBBNetwork@gmail.com"
    else:
        EMAIL_ACCOUNT = email_address

    password = input("Insert password (don't worry we won't tell anyone) :" + "\n")
    if password == "a":
        PASSWORD = "NetworkArchi"
    else:
        PASSWORD = password

    # Update log

    with open("Logs.txt", "a") as file:
        file.write("Connection detected : User = " + EMAIL_ACCOUNT + ", Date = " +
                   str(datetime.now().strftime("%d %m %Y %H:%M:%S")) + "\n")

    file.close()

    load_email()
    set_database()


    while not on_veut_se_tirer:

        cls()

        print("Now logged as " + email_address + " ." + "\n")
        print("INBOX" + "\n\n\n")
        display_mail()

        # -------------------------------------------------------------------
        # ----------------------------MAIN MENU------------------------------
        # -------------------------------------------------------------------

        main_ans = input(
            "E - Exit\n"
            "S - sort e-mails\n"
            "R - Read an email\n"
            "D - Delete an Email\n"
            "L - Logs\n"
            "SF - Save in file\n"
            "W - Write an email"
            "H - Mail Hack the FBI\n")

        on_veut_se_tirer = False

        if main_ans == "E":
            on_veut_se_tirer = True
            # TODO déconnecter
        elif main_ans == "S":
            sort_type_ans = input(
                "Would you like to sort your mail by :\n1 - Date\n2 - Sender\n3 - [TODO] autre tri ?" + "\n")
            if sort_type_ans == "1":
                order_mail_desc("date")
                cls()

            if sort_type_ans == "2":
                order_mail_desc("sender")
                cls()
                display_mail()

        elif main_ans == "R":
            read_id_ans = input(
                "What email would you like to read (insert ID)" + "\n")
            display_mail_detail(read_id_ans)

        elif main_ans == "D":
            del_id_ans = input(
                "What email would you like to read (insert ID)" + "\n")

        elif main_ans == "L":
            with open("Logs.txt", "r") as file:
                logs = file.readlines()
            for line in logs:
                print(line)

        elif main_ans == "SF":
            save_id_ans = input(
                "What email would you like to save in a file (insert ID)" + "\n")
            save_in_file(save_id_ans)

        elif main_ans == "H":
            print("Initiate hacking...")

            for i in range(0, 101, 10):
                print("Hacking the FBI : " + str(i) + "%...")

                time.sleep(1)

            print("FBI successfully hacked, stored in file")

            response = requests.get("https://www.fbi.gov/")

            soup = BeautifulSoup(response.content, "html.parser")

            with open("FBI.html", "wb") as file:

                file.write(soup.prettify().encode('utf-8'))

        elif main_ans == "W":
            cls()
            print("Mode : writing mail")
            to_ans = input("Who to send to ?\n")
            subject_ans = input("Subject :\n")
            text_ans = input("Text:\n")

            if to_ans.split("@")[1] == ("gmail.com" or "Gmail.com"):
                send_email() #TODO brancher le sender
            else:
                temp = 1
                #TODO s'occuper d'autres plates-formes de mail ?




    '''
    set_database()
    load_email()1
    display_mail()
    order_mail_desc("date")
    '''