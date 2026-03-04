# cities-private

Code for generating [Cities of Your Country](https://ankiweb.net/shared/info/48360581) for Anki.

Uses city-or-town and urban-area as well as various subdivisions on Wikidata for each country. Maps are from [these](https://en.wikipedia.org/wiki/Template:Location_map/List) specific "Location maps" which have a formula for generating a dot from the coordinates of the city and the maps are under CC-BY-SA 4.0 licenses. On Wikidata they are linked with the country or subdivision they depict and the cities are linked with the country or subdivision they are located in.
Also uses data from GeoNames and DBpedia, which are both under CC-BY-SA license.

Generates an extensive ordered tag tree-structure like:<br>
`tag:cities::United-Kingdom::England::East-of-England::Essex::Essex::Braintree::Halstead`<br><br>
where it can be used on Anki to select all cities in e.g. England with:<br>
`tag:cities::United-Kingdom::England`<br><br>
covering all the subtags of this tag.

Sources:<br>
- Download and extract allCountries.zip from: https://download.geonames.org/export/dump/