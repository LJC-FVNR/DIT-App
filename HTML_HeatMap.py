from matplotlib import colors
from pandas.io.formats.style import Styler
from pandas.core.indexing import _maybe_numeric_slice, _non_reducing_slice

class HStyler(Styler):
    def relative_luminance(self, rgba) -> float:
        r, g, b = (x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055 ** 2.4) for x in rgba[:3])
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    def min_max_scaler(self, sub=None):
        if sub is None:
            sub = self.subset
        try:
            mini = float(self.data.loc[sub].stack().min())
            maxi = float(self.data.loc[sub].stack().max())
            return (self.data-mini)/(maxi-mini)
        except:
            mini = float(self.data.loc[sub].min())
            maxi = float(self.data.loc[sub].max())
            return (self.data-mini)/(maxi-mini)
    
    def get_heatmap_color(self, value, color_map, text_color_threshold):
        dark = self.relative_luminance(color_map(value)) < text_color_threshold
        text_color = "#f1f1f1" if dark else "#000000"
        color = colors.to_hex(color_map(value))
        return f'background-color: {color};color: {text_color};'

    def get_heatmap(self, cmap, sub=None, text_color_threshold=0.408):
        if sub is None:
            sub = self.subset
        cmap = self.min_max_scaler(sub).applymap(lambda x: self.get_heatmap_color(x, cmap, text_color_threshold))
        sub = _maybe_numeric_slice(self.data, sub)
        sub = _non_reducing_slice(sub)
        c_mapping = lambda x: cmap.loc[sub]
        self.apply(c_mapping, subset=sub, axis=None)
        return self
    
    def format_jump_index(self):
        for i, value in enumerate(self.data.index):
            if value[0] == "<":
                return self
            ida = str(value).replace(" ", "")
            a = f"<a href='#{ida}'>" + value + "</a>"
            self.data.rename(index={value:a}, inplace=True)
            self.index = self.data.index
        return self
    
    def format_jump_columns(self):
        for i, values in enumerate(self.data.columns):
            if len(values) == 1:
                if values[0] == "<":
                    return self
                ida = str(values).replace(" ", "")
                a = f"<a href='#{ida}'>" + values + "</a>"
                self.data.rename(columns={values:a}, inplace=True)
                self.columns = self.data.columns
            else:
                re_map = {}
                for value in values:
                    if value[0] == "<":
                        continue
                    ida = str(value).replace(" ", "")
                    a = f"<a href='#{ida}'>" + value + "</a>"
                    re_map[value] = a
                self.data.rename(columns=re_map, inplace=True)
                self.columns = self.data.columns
        return self