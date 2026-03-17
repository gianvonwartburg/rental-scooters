# Rental Scooters

## Projektbeschreibung

Rental Scooters ist eine webbasierte Anwendung zur Verwaltung und Vermietung von E-Scootern.

Die Anwendung wurde im Rahmen einer Praxisarbeit im Modul Datenbanken und Webentwicklung entwickelt und basiert auf Python und dem Webframework Flask.

Die Plattform unterscheidet zwischen zwei Benutzerrollen:

- **Provider**: verwaltet Scooter und kann Vermietungsstatistiken einsehen
- **Driver**: kann verfügbare Scooter mieten und Mietvorgänge beenden

Zusätzlich stellt die Anwendung eine REST-API zur Verfügung, über welche ausgewählte Daten programmatisch abgefragt werden können.

---

## Live Anwendung

Die Anwendung ist online verfügbar unter:

https://rental-scooters-gian-g7c5bncngrajhad3.westeurope-01.azurewebsites.net

---

## Verwendete Technologien

- Python 3
- Flask
- SQLAlchemy
- PostgreSQL
- Jinja2
- Bootstrap
- Azure App Service
- REST API
- Postman (API Tests)

---

## Funktionsumfang

### Benutzerverwaltung

- Registrierung
- Login / Logout
- Rollenbasierter Zugriff (Provider / Driver)

### Provider Funktionen

- Scooter erstellen
- Scooter bearbeiten
- Scooter löschen
- Scooterstatus verwalten
- Einnahmenübersicht anzeigen

### Driver Funktionen

- verfügbare Scooter anzeigen
- Scooter mieten
- Miete beenden

### REST API

- Tokenbasierte Authentifizierung
- Scooter abrufen
- eigene Rentals abrufen

---

## Autor

Gian von Wartburg  
Praxisarbeit – Datenbanken und Webentwicklung
