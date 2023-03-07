from datetime import datetime


def year(request):
    year = datetime.now().year
    return {'year': year}
