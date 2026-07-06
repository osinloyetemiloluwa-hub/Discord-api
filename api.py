# Inside api.py -> get_messages() function line ~70:
        if request.args.get('search'):
            search_term = f"%{request.args.get('search')}%"
            query = query.filter(Message.content.ilike(search_term)) # Use .ilike for PostgreSQL compatibility
