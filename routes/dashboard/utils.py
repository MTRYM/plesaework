# routes/dashboard/utils.py

from routes.models import User, Rank

def get_chefs_de_groupe():
    return User.query.all()
    
def get_all_ranks():
    return Rank.query.order_by(Rank.level.desc()).all()