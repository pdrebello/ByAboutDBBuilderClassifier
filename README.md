Run the Stanford Core NLP as follows:

```cd stanford-corenlp-full-2018-10-05```

```java -mx6g -cp "*" edu.stanford.nlp.pipeline.StanfordCoreNLPServer -timeout 50000```

Make sure Mongo Client is set up and running. Set configuration appropriately in config.py
Set name of the article db, entitity, and choose a name for the to be created by-about db in config.py

Build the database as follows:

```python BuildDB.py```

There are 3 sections of code - 
BuildDB.py primarily creates the DB, 
classify (called from utils.py) will classify the statements, 
class5 (called from utils.py) will extract the objects of class5 statements.

