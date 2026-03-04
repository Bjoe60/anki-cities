import pandas as pd
import numpy as np
from SPARQLWrapper import SPARQLWrapper, JSON
from file_paths import PROCESSED_FILES

query = """
SELECT ?cityLabel
 ?native
 ?population
 FROM <http://dbpedia.org>
 WHERE { 
	  { SELECT DISTINCT  ?cityLabel
		  (  GROUP_CONCAT (DISTINCT  ?native_,  "|") AS ?native)
		  (  GROUP_CONCAT (DISTINCT  coalesce( ?populationUrban, ?population_, ?populationTotal, ?populationEstimate, ?pop, ?populationMetro),  "|") AS ?population)
		 FROM <http://dbpedia.org>
		 WHERE {  ?city <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://dbpedia.org/ontology/Settlement> .
			 OPTIONAL {  ?city <http://dbpedia.org/ontology/populationUrban> ?populationUrban . }
			 OPTIONAL {  ?city <http://dbpedia.org/ontology/population> ?population_ . }
			 OPTIONAL {  ?city <http://dbpedia.org/ontology/populationTotal> ?populationTotal . }
			 OPTIONAL {  ?city <http://dbpedia.org/property/populationEstimate> ?populationEstimate . }
			 OPTIONAL {  ?city <http://dbpedia.org/property/pop> ?pop . }
			 OPTIONAL {  ?city <http://dbpedia.org/ontology/populationMetro> ?populationMetro . }
			 OPTIONAL {  ?city <http://dbpedia.org/property/nativeName> ?native_ . } ?city <http://www.w3.org/2000/01/rdf-schema#label> ?cityLabel .
			 FILTER (((((( bound( ?native_) ||  bound( ?populationUrban)) ||  bound( ?population_)) ||  bound( ?populationTotal)) ||  bound( ?populationEstimate)) ||  bound( ?pop)) ||  bound( ?populationMetro) )
			 FILTER ( "en" =  lang( ?cityLabel) ) }
		GROUP BY  ?cityLabel
		ORDER BY  ASC ( ?cityLabel) } }
LIMIT  10000
OFFSET  """


sparql = SPARQLWrapper("http://dbpedia.org/sparql", agent='Bjoe1839/1.0 (bjorn60@gmail.com) bot')

def create_dbpedia_dataframe():
	database = []
	offset = 0
	batch_size = 10000
	while True:
		query_offset = query + str(offset)

		sparql.setQuery(query_offset)
		sparql.setReturnFormat(JSON)
		sparql.setTimeout(60000)
		sparql.addExtraURITag("timeout","60000")
		results = sparql.query().convert()
		bindings = results["results"]["bindings"]
		for result in bindings:
			database.append({
				"wikipedia_id": result["cityLabel"]["value"],
				"native": result["native"]["value"] if "native" in result else None,
				"population": result["population"]["value"]
			})
		print(len(database), '/ ~340000')
		if len(bindings) < batch_size:
			break
		offset += batch_size

	df = pd.DataFrame(database)
	df['population'] = np.where(df['population'].str.match(r'\d+'), df['population'], pd.NA)

	df.to_csv(PROCESSED_FILES['DBPedia'], index=False)