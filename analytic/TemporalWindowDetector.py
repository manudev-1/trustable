from typing import List, Tuple
from datetime import datetime, timedelta
import statistics

from model.Review import Review
from analytic.DataParser import DateParser
from model.DetectedPattern import TimeWindow


class TemporalWindowDetector:
    """
    FASE 1: Scansione temporale leggera su TUTTE le recensioni.
    
    Identifica finestre temporali con densità anomalamente alta
    (z-score > soglia) rispetto alla media storica.
    """
    
    DENSITY_ZSCORE_THRESHOLD = 2.0
    WINDOW_SIZES_DAYS = [7, 14, 30]
    MIN_REVIEWS_IN_WINDOW = 3
    
    def __init__(self, reviews: List[Review]):
        """
        Args:
            reviews: Lista di Review object
        """
        self.reviews = reviews
        self.dates = self._extract_and_sort_dates()
    
    def _extract_and_sort_dates(self) -> List[Tuple[datetime, str, int]]:
        """
        Estrae date valide e le sorta.
        
        Returns:
            Lista di tuple (datetime, review_id, rating)
        """
        dates = []
        for review in self.reviews:
            dt = DateParser.parse(review.published_at_iso or review.published_at)
            if dt:
                dates.append((
                    dt,
                    review.review_id or "",
                    review.rating or 3
                ))
        return sorted(dates, key=lambda x: x[0])
    
    def _compute_densities(self, window_size_days: int) -> List[Tuple[float, datetime, datetime]]:
        """
        Calcola densità di recensioni usando finestre mobili.
        
        Args:
            window_size_days: Dimensione della finestra in giorni
        
        Returns:
            Lista di (densità, start_date, end_date) per ogni posizione
        """
        if len(self.dates) < 2:
            return []
        
        densities = []
        
        for i in range(len(self.dates)):
            start_dt = self.dates[i][0]
            end_dt = start_dt + timedelta(days=window_size_days)
            
            count = sum(1 for dt, _, _ in self.dates 
                       if start_dt <= dt <= end_dt)
            
            if count > 0:
                dates_in_window = [dt for dt, _, _ in self.dates 
                                   if start_dt <= dt <= end_dt]
                span_days = (max(dates_in_window) - min(dates_in_window)).days
                
                if span_days == 0:
                    span_days = 1
                
                density = count / (span_days + 1)
                densities.append((density, start_dt, end_dt))
        
        return densities
    
    def detect_anomalous_windows(self) -> List[TimeWindow]:
        """
        Identifica tutte le finestre con z-score > DENSITY_ZSCORE_THRESHOLD
        per qualsiasi dimensione di window.
        
        Returns:
            Lista di TimeWindow anomale
        """
        anomalous_windows = []
        reviewed_intervals = set()
        
        for window_size in self.WINDOW_SIZES_DAYS:
            densities = self._compute_densities(window_size)
            
            if not densities:
                continue

            density_values = [d[0] for d in densities]
            
            if len(density_values) < 2:
                continue
            
            mean_density = statistics.mean(density_values)
            std_density = statistics.stdev(density_values) if len(density_values) > 1 else 0

            for density, start_dt, end_dt in densities:
                if std_density == 0:
                    zscore = 0
                else:
                    zscore = (density - mean_density) / std_density
                
                if zscore > self.DENSITY_ZSCORE_THRESHOLD:
                    reviews_in_window = [
                        (dt, rid, rating) for dt, rid, rating in self.dates
                        if start_dt <= dt <= end_dt
                    ]
                    
                    if len(reviews_in_window) >= self.MIN_REVIEWS_IN_WINDOW:
                        interval_key = (
                            start_dt.date(),
                            end_dt.date(),
                            len(reviews_in_window)
                        )
                        
                        if interval_key not in reviewed_intervals:
                            reviewed_intervals.add(interval_key)
                            
                            window = TimeWindow(
                                start_date=start_dt.strftime("%Y-%m-%d"),
                                end_date=end_dt.strftime("%Y-%m-%d"),
                                total_reviews=len(reviews_in_window),
                                density_zscore=zscore,
                                review_ids=[rid for _, rid, _ in reviews_in_window]
                            )
                            anomalous_windows.append(window)
                            
        return self._deduplicate_windows(anomalous_windows)
    
    @staticmethod
    def _deduplicate_windows(windows: List[TimeWindow]) -> List[TimeWindow]:
        """
        Rimuove finestre ridondanti/overlapping, mantenendo quelle con zscore più alto.
        """
        if not windows:
            return []
        
        windows_sorted = sorted(windows, key=lambda w: w.density_zscore, reverse=True)
        kept = []
        
        for window in windows_sorted:
            overlaps = False
            for kept_window in kept:
                if (window.start_date == kept_window.start_date or 
                    window.end_date == kept_window.end_date):
                    overlaps = True
                    break
            
            if not overlaps:
                kept.append(window)
        
        return sorted(kept, key=lambda w: w.start_date)
