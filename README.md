Automatisches Update einer (Sub-)Domain bei Cloudflare, wenn sich die öffentliche IP-Adresse ändert.

## Voraussetzungen

- Cloudflare-Account mit Zugriff auf die Domain
- Cloudflare **API Token** mit Berechtigung für DNS-Änderungen (`Zone.DNS`)
- `curl`, `jq`, und Bash auf deinem Server installiert

## Einrichtung

1. **API Token generieren**  
   - Gehe zu [Cloudflare Dashboard](https://dash.cloudflare.com/profile/api-tokens).
   - Erstelle einen neuen Token mit mind. **Zone.DNS:Edit** und **Zone.DNS:Read** für die gewünschte Zone.

2. **Zone ID ermitteln**  
   - Im Cloudflare Dashboard unter `Domain > Overview` → **API Zone ID** kopieren.

3. **Skript anpassen**  
   Trage folgende Variablen im Skript ein:
   ```bash
   CLOUDFLARE_API_TOKEN="dein-token"
   ZONE_ID="deine-zone-id"
   RECORD_NAME="sub.domain.tld"   # oder *.domain.tld für Wildcard
   RECORD_TYPE="A"                # Für IPv4, AAAA für IPv6

## Installation

1. **Abhängigkeiten installieren:**
    ```bash
    sudo apt update && sudo apt install curl jq -y
    ```

2. **Skript bereitstellen und ausführbar machen:**
    ```bash
    sudo cp cloudflare-ddns.sh /usr/local/bin/cloudflare-ddns.sh
    sudo chmod +x /usr/local/bin/cloudflare-ddns.sh
    ```

3. **Logfile anlegen:**
    ```bash
    sudo touch /var/log/cloudflare-ddns.log
    sudo chmod 666 /var/log/cloudflare-ddns.log
    ```


4. **Cronjob einrichten:**
    ```bash
    crontab -e
    ```
    Füge folgende Zeile hinzu (alle 10 Minuten ausführen):
    ```
    */10 * * * * /usr/local/bin/cloudflare-ddns.sh
    ```

## Hinweise

- `"proxied": false` im Skript → **nur DNS** (graue Wolke, kein Proxy)
- Das Skript loggt nach `/var/log/cloudflare-ddns.log`
- Nur A- oder AAAA-Records werden aktualisiert

## Beispielausgabe

Hinweise
	•	Das Skript aktualisiert den angegebenen A/AAAA-Record nur, wenn sich die IP geändert hat.
	•	Die Einstellung "proxied": false sorgt dafür, dass kein Cloudflare-Proxy (graue Wolke) genutzt wird.
	•	Für Subdomains oder Wildcards einfach RECORD_NAME entsprechend anpassen.

Troubleshooting
	•	Prüfe das Logfile /var/log/cloudflare-ddns.log bei Fehlern.
	•	Stelle sicher, dass der API-Token die richtigen Rechte hat.
	•	Bei Problemen mit jq oder curl: Version prüfen.
