import sqlite3
import smtplib
import imaplib
import email
import datetime

DOMAIN = 'imap.gmail.com'
EMAIL_ACCOUNT = "AAABBBNetwork@gmail.com"
PASSWORD = "NetworkArchi"


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
            local_date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
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
        print(row)

    conn.commit()

    conn.close()


if __name__ == "__main__":
    set_database()
    load_email()
    display_mail()
    order_mail_desc("date")