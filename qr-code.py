import string
import random
import segno

def generer_chaine_aleatoire(longueur):
    caracteres = string.ascii_lowercase
    return ''.join(random.choice(caracteres) for _ in range(longueur))

chaine_aleatoire = generer_chaine_aleatoire(10)
print("La chaîne aléatoire est :", chaine_aleatoire)

qrcode = segno.make_qr(chaine_aleatoire)
qrcode.save("basic_qrcode.png")