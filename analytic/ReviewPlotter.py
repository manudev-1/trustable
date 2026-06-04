from typing import List
from matplotlib import pyplot as plt

from model.Review import Review
from analytic.DataParser import DateParser
from analytic.TemporalAnalyzer import TemporalAnalyzer

class ReviewPlotter:
    """Visualizzazione grafica delle recensioni"""
    
    def __init__(self, reviews: List[Review]):
        self.reviews = reviews
    
    def show_timeline(self) -> None:
        """Mostra un grafico a dispersione delle recensioni nel tempo"""
        data = []
        ratings = []
        
        for review in self.reviews:
            dt = DateParser.parse(review.published_at_iso or review.published_at)
            if dt and review.rating:
                data.append(dt)
                ratings.append(review.rating)
        
        if not data:
            print("Nessun dato valido per il grafico")
            return
        
        plt.figure(figsize=(14, 6))
        plt.scatter(data, ratings, alpha=0.6, c=ratings, cmap='RdYlGn')
        
        plt.yticks([1, 2, 3, 4, 5])
        plt.xlabel("Data")
        plt.ylabel("Rating")
        plt.title(f"Recensioni nel tempo ({len(data)} recensioni)")
        plt.colorbar(label="Rating")
        plt.grid(alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def show_monthly_histogram(self) -> None:
        """Mostra un istogramma delle recensioni per mese"""
        analyzer = TemporalAnalyzer(self.reviews)
        density = analyzer.get_monthly_density()
        
        if not density:
            print("Nessun dato per l'istogramma")
            return
        
        months = list(density.keys())
        counts = list(density.values())
        
        plt.figure(figsize=(12, 5))
        bars = plt.bar(months, counts, color='steelblue', alpha=0.7)
        plt.xlabel("Mese")
        plt.ylabel("Numero di recensioni")
        plt.title("Distribuzione mensile delle recensioni")
        plt.xticks(rotation=45, ha='right')
        
        for bar, count in zip(bars, counts):
            if count > 0:
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        str(count), ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.show()
