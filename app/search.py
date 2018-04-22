from flask import current_app

def add_to_index(index, model):
    if not current_app.elasticsearch:
        return # None
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, doc_type=index, id=model.id, body=payload)
    # new posts versus existing posts
    # "model" refers to individual object in the table
    # possible to index the same post twice?
    # payload is dictionary with key 'body'

def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, doc_type=index, id=model.id)
    # or delete the index altogether

def query_index(index, query, page, per_page):
    if not current_app.elasticsearch:
        return [], 0 # consistent with return statement below
    search = current_app.elasticsearch.search(
        index=index, doc_type=index,
        body={'query': {'multi_match': {'query': query, 'fields': ['*']}},
              'from': (page - 1) * per_page, 'size': per_page})
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    # WHY NOT ids = [hit['_source']['body'] for hit in search['hits']['hits']]
    return ids, search['hits']['total']
    # ids is list, in descending order by _score
    # search is JSON/nested dictionary
    # per_page = current_app.config['POSTS_PER_PAGE']?

# not saving search queries in the database