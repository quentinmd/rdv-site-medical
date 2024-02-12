from datetime import datetime

# Exemple de chaîne de caractères représentant une date et une heure
date_str = "2024-02-07 10:30:00"

# Convertir la chaîne en objet datetime
date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

# Maintenant, vous pouvez utiliser strftime pour formater la date comme vous le souhaitez
formatted_date = date_obj.strftime("%d %B %Y à %H:%M")

print(formatted_date)  # Affichera : 07 février 2024 à 10:30