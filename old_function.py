def _build_delta(self, data: CompleteData) -> DeltaAnalysis:
        """Delta analizi oluştur"""
        financial = data.financial
        periods = financial.periods_sorted[:5]
        
        rows = []
        for key, label in [('favok_margin_pct', 'FAVOK Marji %'), ('net_debt_favok', 'Net Borc/FAVOK'),
                          ('roic_pct', 'ROIC %'), ('current_ratio', 'Cari Oran'), ('fcf_net_income_pct', 'FCF/NetKar %')]:
            values = []
            for p in periods[:5]:
                val = getattr(p, key, None) if hasattr(p, key) else None
                values.append({'per