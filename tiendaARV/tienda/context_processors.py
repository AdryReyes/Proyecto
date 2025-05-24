from .models import Categoria

def categorias_context(request):
    categorias = Categoria.objects.filter(producto__isnull=False).distinct()
    return {'categorias': categorias}


