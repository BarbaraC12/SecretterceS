import os
import sys
import json
import random
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class SecretSanta:
    def __init__(self, fichier='secret_santa.json'):
        self.fichier = fichier
        self.participants = self.load_santa()

    def load_santa(self):
        try:
            with open(self.fichier, 'r') as fichier:
                return json.load(fichier)
        except FileNotFoundError:
            return []

    def save_santa(self):
        with open(self.fichier, 'w') as fichier:
            json.dump(self.participants, fichier, indent=2)

    def exist(self, lname, name, mail):
        for personne in self.participants:
            if personne['lname'] == lname and personne['name'] == name:
                print(f"{lname} {name} existe déjà dans la liste.")
                return True
            elif 'mail' in personne and personne['mail'] == mail:
                print(f"L'adresse e-mail {mail} existe déjà dans la liste.")
                return True
        return False

    def ask_info(self):
        lname = input('Quel est ton nom? ').capitalize()
        name = input('Quel est ton prenom? ').capitalize()
        mail = input('Quel est ton adresse mail? ').lower()
        # ask 3 wish
        wishlist = []
        max_wish = 3
        for i in range(1, max_wish + 1):
            wish = input(f'Que souhaiterai tu pour noël? {i}/{max_wish} >')
            if wish == '':
                break
            wishlist.append(wish)
        # ask hobbies
        hobbies = input('Quels sont tes hobbies? (separés par des virgules)')
        return lname, name, mail, wishlist, hobbies

    def add_santa(self):
        lname, name, mail, wish, hobbies = self.ask_info()
        if not self.exist(lname, name, mail):
            nouvelle_personne = {
                'lname': lname,
                'name': name,
                'mail': mail,
                'wish': wish,
                'hobbies': hobbies
            }
            self.participants.append(nouvelle_personne)
            self.save_santa()
            print(f"{lname} {name} a été ajouté avec succès à la liste.")
        else:
            print("Erreur : cette personne est déja présente dans la liste.")

    def assign_santa(self):
        if len(self.participants) < 3:
            print("Le tirage au sort impossible avec moins de 3 participants.")
            return
        participants_copies = self.participants.copy()
        for personne in self.participants:
            dest = random.choice(participants_copies)
            # Assurez-vous que la personne ne s'offre pas un cadeau à elle-même
            while dest == personne:
                dest = random.choice(participants_copies)
            personne['dest'] = {
                'lname': dest['lname'],
                'name': dest['name'],
                'mail': dest['mail'],
                'wishlist': dest['wish'],
                'hobbies': dest['hobbies']
            }
            dest.pop('wish', None)
            dest.pop('hobbies', None)
            participants_copies.remove(dest)
        self.save_assign()

    def save_assign(self):
        with open('secret_santa_attribue.json', 'w') as fichier:
            json.dump(self.participants, fichier, indent=2)

    def envoyer_emails(self, smtp_name, smtp_port, mailer, mail_pwd):
        for personne in self.participants:
            dest = personne['dest']
            message = MIMEMultipart()
            message['From'] = mailer
            message['To'] = dest['email']
            message['Subject'] = "Secret Santa X Dualboot 2023"
            corps_message = f"""
            Hello little secret Santa {personne['name']},

            le tirage au sort t'a designer comme le secret Santa de {
                dest['name']} {dest['lname']}!

            Voici quelques informations utiles à son sujet:
            - Sa wishlist : {dest.get('wishlist', 'Non-renseigner')}
            - Ses hobbies : {dest.get('hobbies', 'Non-renseigner')}

            N'oublie pas de garder le secret pour faire de ce Noël une expérience spéciale!

            Cordialement,
            Votre organisateur Secret Santa
            """

            message.attach(MIMEText(corps_message, 'plain'))

            # Connexion au serveur SMTP de Gmail
            with smtplib.SMTP_SSL(smtp_name, smtp_port) as server:
                server.login(mailer, mail_pwd)

                # Envoi de l'e-mail
                server.sendmail(mailer, dest['email'], message.as_string())

            print(f"E-mail envoyé à {personne['prenom']} {personne['nom']}.")


len_arg = len(sys.argv)
secret_santa = SecretSanta()
load_dotenv()
if len_arg < 2 or sys.argv[1] == 'add':
    secret_santa.add_santa()
elif len_arg == 2:
    arg = sys.argv[1]
    if arg == 'assign':
        secret_santa.assign_santa()
    elif arg == 'send':
        smtp_name = os.getenv('SMTP_SERVER')
        smtp_port = int(os.getenv('SMTP_PORT'))
        mailer = os.getenv('SENDER_EMAIL')
        mail_pwd = os.getenv('SENDER_PASSWORD')
        secret_santa.envoyer_emails(smtp_name, smtp_port, mailer, mail_pwd)
