# Iekārtu datu apstrāde caur MQTT protokolu

Risinājums telemetrijas datu uztveršanai no MQTT, datu kvalitātes pārbaudei, normalizēšanai un strukturētai uzglabāšanai PostgreSQL datubāzē.

Sistēma paredzēta dažādu tipu iekārtām un dažādiem datu formātiem, vienlaikus nodrošinot klientu datu nošķirtību vienā RabbitMQ brokerī.

## Par risinājumu

Datu apstrādes plūsma:

Iekārta
  ↓ MQTT
RabbitMQ brokeris
  ↓ durable AMQP queue
Python consumer
  ↓
Datu formāta identificēšana
  ↓
Iekārtas/vendor-specific parser
  ↓
Vienots mērījumu formāts
  ↓
Datu kvalitātes pārbaude
  ↓
PostgreSQL


Izmantotās tehnoloģijas:

* Python 3.12
* RabbitMQ
* MQTT
* AMQP
* PostgreSQL
* Docker / Docker Compose
* pytest

---

# Quick Start

## 1. Izveidot `.env` failu

Windows PowerShell:
Copy-Item .env.example .env


`.env.example` satur tikai demo/development konfigurāciju.

## 2. Palaist visu sistēmu

docker compose up -d


Šī komanda palaiž:


mqtt_postgres
mqtt_rabbitmq
mqtt_consumer


## 3. Pārbaudīt servisu statusu


docker compose ps


PostgreSQL un RabbitMQ jābūt `healthy`, bet `mqtt_consumer` jābūt `running`.

## 4. Nosūtīt testa MQTT ziņojumu


python -m src.mqtt_test_publisher


## 5. Apskatīt Python consumer rezultātu


docker logs mqtt_consumer --tail 20


## 6. Palaist automatizētos testus


python -m pytest -v


## Sistēmas apturēšana

docker compose down


Šī komanda aptur konteinerus, bet saglabā PostgreSQL un RabbitMQ Docker volumes.



# Arhitektūra

## RabbitMQ un MQTT

RabbitMQ darbojas kā MQTT brokeris, caur kuru iekārtas nosūta telemetrijas datus.

MQTT topic struktūra:

clients/{client}/buildings/{building}/devices/{device}/telemetry


Piemērs:

clients/demo/buildings/test/devices/24e124725d021011/telemetry


No topic iespējams identificēt:


client
building
device


Piemēram:


clients/demo/buildings/test/devices/24e124725d021011/telemetry

client   = demo
building = test
device   = 24e124725d021011


RabbitMQ ienākošos MQTT ziņojumus novirza uz durable AMQP rindu:

telemetry_ingestion


Python consumer nolasa ziņojumus no šīs rindas.

Šāds risinājums atdala datu saņemšanu no datu apstrādes. Ja Python consumer uz laiku nav aktīvs, dati var palikt rindā un tikt apstrādāti pēc consumer darbības atjaunošanas.



# Python consumer

Galvenais consumer:

src/consumers/rabbitmq_consumer.py


Tā uzdevumi:

1. Saņemt ziņojumu no RabbitMQ AMQP queue.
2. No routing key noteikt klientu, ēku un iekārtu.
3. Nolasīt JSON payload.
4. Noteikt atbilstošo parser.
5. Normalizēt iekārtai specifisko datu struktūru.
6. Pārbaudīt datu kvalitāti.
7. Saglabāt raw message un strukturētus mērījumus PostgreSQL.
8. Acknowledge RabbitMQ ziņojumu pēc veiksmīgas apstrādes.

Ja ziņojuma apstrāde neizdodas, oriģinālais payload un kļūdas apraksts tiek saglabāts datubāzē turpmākai analīzei.



# Datu struktūra un parseri

Uzdevumā dotās iekārtas izmanto savstarpēji atšķirīgas JSON struktūras.

Tāpēc RabbitMQ consumer un datubāzes slānis nav piesaistīts konkrētam ražotājam.

Vendor-specific parseri pārveido dažādos datu formātus vienotā iekšējā formātā.

Parser router:

src/parsers/router.py


Pašreizējie parser moduļi:

src/parsers/milesight.py
src/parsers/wago.py
src/parsers/viltrus.py


Katrs parser rezultātā izveido vienotus `Measurement` objektus.

Piemēram, neatkarīgi no sākotnējā datu formāta rezultāts var būt:

datapoint   = temperature
value       = 22.1
measured_at = 2025-06-30T12:32:42Z


# Atbalstītie datu piemēri

Risinājums izstrādāts un testēts ar uzdevumam pievienotajiem reālajiem datu piemēriem.


# Datu kvalitāte un ticamība

Pirms mērījuma saglabāšanas strukturētajā datu tabulā tam tiek noteikts quality statuss.

Iespējamie statusi:

valid
suspicious
invalid


Piemēri AM103 sensoram:


humidity = 48
→ valid



humidity = 148



temperature = 62.1
→ suspicious


Pašreizējā implementācijā tiek pārbaudīti vairāki datu kvalitātes aspekti:

* obligāto lauku esamība;
* datu tips;
* datu formāts;
* timestamp parsējamība;
* saprātīgi vērtību diapazoni zināmiem datu punktiem;
* nederīgs JSON;
* neatbilstība starp device ID topic un payload;
* dublikātu aizsardzība datubāzes līmenī.

### Dublikāti

`measurements` tabulā unikālu mērījumu nosaka kombinācija:


device
+
datapoint
+
measured_at


Tas novērš viena un tā paša mērījuma atkārtotu ierakstīšanu, ja tas tiek apstrādāts vairākas reizes.

### Validācijas diapazoni

Pašreizējie fizisko vērtību diapazoni ir pieņēmumi, lai demonstrētu datu kvalitātes pārbaudes mehānismu.

Production vidē datu punktu:

* unit;
* scale;
* datatype;
* allowed values;
* minimum;
* maximum

būtu jādefinē, izmantojot konkrētās iekārtas dokumentāciju.

### Laika zīmogu hronoloģija

Parseri pārbauda un normalizē saņemto timestamp formātu, un dublikātu ierobežojumi novērš viena un tā paša datu punkta atkārtotu saglabāšanu vienā laikā.

Pilna starp secīgiem ziņojumiem veicama hronoloģijas/anomaly pārbaude būtu viens no nākamajiem production uzlabojumiem.


# Raw data saglabāšana

Sistēma saglabā gan:

oriģinālo MQTT payload


gan:

normalizētus measurements


Tam ir divi atšķirīgi mērķi.

## `measurements`

Paredzēta ērtai:

* vizualizācijai;
* monitorēšanai;
* statistiskai analīzei;
* automatizācijas procesiem.

## `raw_messages`

Saglabā oriģināli saņemto informāciju.

Tas nodrošina izsekojamību.

Ja vēlāk tiek konstatēta kļūda parser vai interpretācijas loģikā, iespējams pārbaudīt, ko iekārta faktiski bija nosūtījusi.

Arī malformed payload netiek vienkārši izmests.

Kļūdas gadījumā tiek saglabāts:

* MQTT topic;
* oriģinālais payload;
* processing status;
* error message;
* saņemšanas laiks.



# PostgreSQL datubāzes struktūra

Galvenā loģiskā hierarhija:

Klients
  ↓
Ēka
  ↓
Iekārta
  ↓
Raw messages
  ↓
Measurements

## `clients`

Glabā klientus/organizācijas.

## `buildings`

Glabā klienta ēkas.



## `devices`

Glabā iekārtu metadata:

* external device ID;
* name;
* manufacturer;
* model;
* device type;
* source type.

Ja no zināma klienta/ēkas saņemts ziņojums no jaunas atbalstīta tipa iekārtas, device ieraksts var tikt izveidots automātiski.

## `raw_messages`

Glabā oriģinālos saņemtos payload un apstrādes rezultātu.

## `measurements`

Glabā normalizētos datu punktus.

Mērījuma vērtība atkarībā no datu tipa var tikt saglabāta kā:

numeric_value
text_value
boolean_value

Papildus tiek saglabāts:

measured_at
quality


## `datapoint_definitions`

Tabula paredzēta datu punktu metadata un nākotnes konfigurācijai, piemēram:

* description;
* value type;
* unit;
* scale;
* minimum value;
* maximum value.



# Timestamp apstrāde

Dažādi datu avoti izmanto dažādus timestamp formātus.

Ja timestamp jau satur timezone/UTC informāciju, tā tiek saglabāta atbilstoši norādītajam laikam.

Ja timezone nav norādīta, tiek izmantota konkrētās ēkas konfigurācija.


## Pieņēmumi

WAGO un Viltrus piemēros timestamp nenorāda timezone.

Tāpēc šajā risinājumā šie timestamp tiek interpretēti kā ēkas lokālais laiks.

Zenner piemērā tiek pieņemts, ka `hour` vērtība attiecas uz ēkas lokālo laiku.

Production vidē šie pieņēmumi būtu jāpārbauda pret ražotāja dokumentāciju.


# Nezināmi mērogi un mērvienības

Dažiem uzdevumā dotajiem datu punktiem nav pievienota pietiekama metadata, lai droši noteiktu mērvienību vai scaling.

Piemēram:
Temp_SupplyAir = 201
Setpoint_SupplyAirTemp = 200
Setpoint_Humidity = 500


Tāpēc risinājums neveic nepamatotu konversiju un saglabā raw value tieši tādu, kādu to nosūtījusi iekārta.

Production vidē scaling un unit konfigurācija būtu jāveido no ražotāja register/device dokumentācijas.



# Drošība un klientu datu nošķirtība

Uz viena RabbitMQ brokera iespējams apkalpot vairākus klientus.

Klientiem tiek izmantoti atsevišķi MQTT lietotāji un topic namespace.

Piemēram, demo klienta namespace:


clients/demo/...


Demo lietotājs:

client_demo

drīkst publicēt:

clients/demo/...


bet nedrīkst publicēt:

clients/other/...


Šis ierobežojums tiek realizēts RabbitMQ līmenī ar:

authentication
permissions
topic permissions


nevis tikai Python application līmenī.

Tika veikts arī negatīvais drošības tests, kurā `client_demo` autentificējas brokerī, bet mēģina publicēt cita klienta namespace.

RabbitMQ šādu darbību noraida ar authorization error.

Backend Python consumer izmanto atsevišķu RabbitMQ lietotāju.


# RabbitMQ konfigurācija

RabbitMQ konfigurācija atrodas:

rabbitmq/
├── definitions.json
├── enabled_plugins
└── rabbitmq.conf

Tajā tiek definēti:

* MQTT plugin;
* lietotāji;
* permissions;
* topic permissions;
* `telemetry_ingestion` queue;
* routing/binding konfigurācija.

RabbitMQ palaišanas laikā importē `definitions.json`.

Tas ļauj nepieciešamo broker konfigurāciju reproducēt arī jaunā vidē.



# Automātiska sistēmas palaišana

Visa sistēma tiek pārvaldīta ar Docker Compose.

Tiek palaisti trīs servisi:

mqtt_postgres
mqtt_rabbitmq
mqtt_consumer


PostgreSQL un RabbitMQ ir konfigurēti healthchecks.

Python consumer tiek palaists tikai pēc tam, kad abas nepieciešamās komponentes ir pieejamas.

Consumer izmanto:

restart: unless-stopped


Tas nozīmē, ka consumer automātiski tiek palaists atkārtoti pēc kļūmes vai Docker/server restartēšanas, ja tas nav manuāli apturēts.



# PostgreSQL sākotnējā inicializācija

Datubāzes shēma atrodas:

database/schema.sql


Docker Compose to mounto PostgreSQL initialization directory.

Ja tiek izveidots jauns PostgreSQL volume, shēma tiek izveidota automātiski pie pirmās datubāzes palaišanas.



# MQTT testa publisheri

Projektā atrodas vairāki test publisheri:

src/mqtt_test_publisher.py
src/mqtt_test_uc300.py
src/mqtt_test_vicki.py
src/mqtt_test_zenner.py
src/mqtt_test_wago.py
src/mqtt_test_wago_plc.py
src/mqtt_test_wago_ahu.py
src/mqtt_test_viltrus.py


# Automatizētie testi

Parser un validation testi izmanto `pytest`.

Palaist:

python -m pytest -v


Testi pārbauda, piemēram:

* AM103 parsing;
* WAGO parsing;
* Viltrus column mapping;
* normālu temperature value;
* suspicious temperature;
* invalid humidity;
* low battery;
* invalid CO₂.


# RabbitMQ Management

RabbitMQ Management interface lokāli pieejams:

http://localhost:15672

Tajā iespējams apskatīt:

* connections;
* exchanges;
* queues;
* consumers;
* message rates;
* users.



# Galvenie arhitektūras lēmumi

## Kāpēc dati tiek normalizēti?

Uzdevumā dotajām iekārtām ir būtiski atšķirīgas JSON struktūras.

Vendor-specific parseri pārveido tās vienotā `Measurement` formātā.

Tādējādi datubāzes un validation slāņiem nav jāzina katra ražotāja datu struktūra.


## Kāpēc saglabāt arī raw messages?

Normalizētos datus ir ērti izmantot vizualizācijai, monitorēšanai un statistikā.

Raw messages nodrošina iespēju vēlāk pārbaudīt sākotnēji saņemto informāciju un atkārtoti interpretēt datus, ja parser loģika tiek mainīta.


## Kāpēc izmantot AMQP queue?

Queue atdala MQTT datu saņemšanu no Python apstrādes procesa.

Ja consumer uz laiku nav aktīvs, dati var uzkrāties RabbitMQ rindā un tikt apstrādāti pēc consumer darbības atjaunošanas.


## Kāpēc izmantot topic permissions?

Klientu datu nošķirtībai jānotiek jau MQTT/RabbitMQ līmenī.

Klientam nevajadzētu būt iespējai publicēt vai piekļūt cita klienta datiem pat tad, ja Python application vēl nav saņēmis attiecīgo ziņojumu.

