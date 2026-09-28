import pandas as pd

# --- Настройки ---
input_file = '1.xlsx'          # Входной Excel
output_tex = 'mapping.tex'  # Выходной LaTeX

# --- 1. Читаем Excel ---
df = pd.read_excel(input_file, header=0)

# --- 2. Формируем строки таблицы ---
rows_list = []

for index, row in df.iterrows():
    name = str(row['Наименование']).strip()
    do_part = str(row['DO']).strip()
    da_part = str(row['DA']).strip()

    # Пропускаем пустые строки
    if not name or name == 'nan':
        continue

    # Склеиваем адрес МЭК 61850
    address = f"{do_part}.{da_part}"

    # Экранируем спецсимволы LaTeX
    safe_address = (address
                    .replace('\\', r'\textbackslash{}')
                    .replace('_', r'\_')
                    .replace('&', r'\&')
                    .replace('%', r'\%')
                    .replace('#', r'\#')
                    .replace('$', r'\$')
                    .replace('{', r'\{')
                    .replace('}', r'\}'))

    safe_name = (name
                 .replace('\\', r'\textbackslash{}')
                 .replace('_', r'\_')
                 .replace('&', r'\&')
                 .replace('%', r'\%')
                 .replace('#', r'\#')
                 .replace('$', r'\$')
                 .replace('{', r'\{')
                 .replace('}', r'\}'))

    rows_list.append(f"{safe_address} & {safe_name} \\\\\n\\hline")

all_rows = "\n".join(rows_list)

# --- 3. Шаблон LaTeX (используем маркер для подстановки) ---
tex_template = r"""
\color{unimain}{\section[(справочное) Сопоставление сигналов устройства с моделью МЭК~61850]{(справочное)\\Сопоставление сигналов устройства с моделью МЭК 61850}\label{app:mapping}}
\color{black}

\medskip
\setlength{\extrarowheight}{0.06cm}

\par
Сопоставление сигналов устройства в соответствии с моделью МЭК 61850 приведены в таблице \ref{app_set:mapping}.
\begin{longtable}{|>{\raggedright\arraybackslash}m{0.5\textwidth}|>{\raggedright\arraybackslash}m{0.45\textwidth}|}
% Первая страница: полный заголовок
\caption{Сопоставление сигналов в соответствии с моделью МЭК 61850\hfill\vspace{-0.5\baselineskip}}\label{app_set:mapping}\\
\hline
\rowcolor{unimain!40}
\multicolumn{1}{|>{\centering\arraybackslash}m{0.5\textwidth}|}{\textbf{Адрес МЭК 61850}} & \multicolumn{1}{>{\centering\arraybackslash}m{0.45\textwidth}|}{\textbf{Наименование сигнала}} \\
\hline
\endfirsthead

% Промежуточные страницы: «Продолжение таблицы»
\caption*{\hspace{3pt}\emph{Продолжение таблицы \ref{app_set:mapping}\hfill\vspace{-0.5\baselineskip}}} \\
\hline
\rowcolor{unimain!40}
\multicolumn{1}{|>{\centering\arraybackslash}m{0.5\textwidth}|}{\textbf{Адрес МЭК 61850}} & \multicolumn{1}{>{\centering\arraybackslash}m{0.45\textwidth}|}{\textbf{Наименование сигнала}} \\
\hline
\endhead

%%ROWS_PLACEHOLDER%%
\end{longtable}
"""

final_tex = tex_template.replace('%%ROWS_PLACEHOLDER%%', all_rows)

# --- 4. Записываем результат ---
with open(output_tex, 'w', encoding='utf-8') as f:
    f.write(final_tex)

print(f"Готово! Файл '{output_tex}' создан.")
print(f"Вставлено строк: {len(rows_list)}")