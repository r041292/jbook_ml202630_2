"""Notación matemática de los modelos, con la misma notación del informe jbook_dashboard.

Las ecuaciones de SVR RBF, Kernel Ridge, TR-KRR, DenseWeight, TCR y del kernel de GPR–XGBoost
se copian del jbook (03 a 05). Para los modelos cuyo jbook solo los describe en palabras se añade
la formulación estándar del artículo de referencia, sin parámetros propios del proyecto.
"""
from dash import dcc, html

# Clave del dashboard -> Markdown con LaTeX. Claves de los clásicos y del catálogo «Originales».
MATH = {
    'svm': r'''
La regresión de vectores de soporte con pérdida $\varepsilon$-insensible (`LinearSVR`) ajusta una función lineal
$f(x)=w^\top x+b$ sobre las variables transformadas $x$ resolviendo

$$
\min_{w,b}\ \tfrac{1}{2}\lVert w\rVert^2 + C\sum_{i=1}^{n}\max\!\big(0,\ \lvert y_i - f(x_i)\rvert - \varepsilon\big).
$$

Los errores menores que $\varepsilon$ no se penalizan; los mayores se penalizan linealmente con peso $C$.

**Forma primal (se minimiza)**, con variables de holgura $\xi_i,\xi_i^*\ge 0$:

$$
\min_{w,b,\xi,\xi^*}\ \tfrac{1}{2}\lVert w\rVert^2 + C\sum_{i=1}^{n}(\xi_i+\xi_i^*)
\quad\text{s.a.}\quad
\begin{cases} y_i - w^\top x_i - b \le \varepsilon+\xi_i\\ w^\top x_i + b - y_i \le \varepsilon+\xi_i^*\end{cases}
$$

**Forma dual (se maximiza)** con el **kernel lineal** $k(x,x')=x^\top x'$:

$$
\max_{\alpha,\alpha^*}\ -\tfrac{1}{2}\sum_{i,j}(\alpha_i-\alpha_i^*)(\alpha_j-\alpha_j^*)\,k(x_i,x_j)
-\varepsilon\sum_i(\alpha_i+\alpha_i^*)+\sum_i y_i(\alpha_i-\alpha_i^*),
$$

$$
\text{s.a.}\quad \sum_i(\alpha_i-\alpha_i^*)=0,\qquad 0\le\alpha_i,\alpha_i^*\le C,
\qquad w=\sum_i(\alpha_i-\alpha_i^*)\,x_i .
$$
''',
    'knn': r'''
Con la distancia de Minkowski de orden $p$ entre estudiantes escalados,

$$
d_p(x, x') = \Big(\sum_{j}\lvert x_j - x'_j\rvert^{p}\Big)^{1/p},
$$

la predicción promedia la nota de los $k$ vecinos más cercanos $N_k(x)$, opcionalmente con pesos por cercanía $w_i = 1/d_p(x, x_i)$:

$$
\hat{y}(x) = \frac{\sum_{i\in N_k(x)} w_i\, y_i}{\sum_{i\in N_k(x)} w_i},\qquad w_i = 1 \text{ si los pesos son uniformes.}
$$
''',
    'ridge': r'''
Mínimos cuadrados con penalización L2 sobre los coeficientes:

$$
\hat\beta = \arg\min_{\beta}\ \sum_{i=1}^{n}\big(y_i - \beta_0 - x_i^\top\beta\big)^2 + \alpha\,\lVert\beta\rVert_2^2
\;=\; (X^\top X + \alpha I)^{-1}X^\top y .
$$

Un `alpha` mayor encoge todos los coeficientes hacia cero sin anularlos.
''',
    'lasso': r'''
Mínimos cuadrados con penalización L1, que puede anular coeficientes:

$$
\hat\beta = \arg\min_{\beta}\ \frac{1}{2n}\sum_{i=1}^{n}\big(y_i - \beta_0 - x_i^\top\beta\big)^2 + \alpha\,\lVert\beta\rVert_1 .
$$

La norma $\lVert\beta\rVert_1=\sum_j\lvert\beta_j\rvert$ realiza la selección de variables.
''',
    'forest': r'''
Promedio de $B$ árboles entrenados con remuestreo bootstrap y un subconjunto aleatorio de variables en cada división
(`max_features = 0,7`):

$$
\hat{y}(x) = \frac{1}{B}\sum_{b=1}^{B} T_b(x).
$$
''',
    'xgboost': r'''
Suma aditiva de $K$ árboles poco profundos, $\hat{y}_i=\sum_{k=1}^{K} f_k(x_i)$, que minimiza un objetivo regularizado:

$$
\mathcal{L} = \sum_{i=1}^{n} \ell(y_i, \hat{y}_i) + \sum_{k=1}^{K}\Omega(f_k),\qquad
\Omega(f) = \gamma\,T + \tfrac{1}{2}\lambda\sum_{j=1}^{T} w_j^2 ,
$$

con $T$ hojas y pesos de hoja $w_j$. Cada árbol se ajusta con el gradiente $g_i$ y la hessiana $h_i$ de la pérdida; en una hoja $j$ con observaciones $I_j$, el peso óptimo es

$$
w_j^{*} = -\frac{\sum_{i\in I_j} g_i}{\sum_{i\in I_j} h_i + \lambda}.
$$
''',
    'decision_tree': r'''
Árbol CART de regresión: cada división binaria elige variable $j$ y umbral $s$ que minimizan el error cuadrático de los grupos resultantes,

$$
\min_{j,\,s}\Big[\sum_{x_i\in R_1(j,s)}(y_i-\bar y_{R_1})^2 + \sum_{x_i\in R_2(j,s)}(y_i-\bar y_{R_2})^2\Big],
$$

y cada hoja $R$ predice la media $\bar y_R$ de su grupo. La poda por costo-complejidad ($\alpha$ = `ccp_alpha`) minimiza $\sum_{R}\sum_{x_i\in R}(y_i-\bar y_R)^2+\alpha\,\lvert T\rvert$.
''',
    'm0': r'''
La función aprendida minimiza la misma pérdida $\varepsilon$-insensible del SVM, pero el producto interno se sustituye por el **kernel gaussiano (RBF)**,

$$
k(x, x') = \exp\!\big(-\gamma\,\lVert x - x'\rVert^2\big),
$$

de modo que

$$
f(x)=\sum_i(\alpha_i-\alpha_i^*)\,k(x_i,x)+b ,
$$

con coeficientes distintos de cero solo en los vectores de soporte (error mayor o igual que $\varepsilon$).

**Notación del kernel.** $\phi$ es la transformación implícita al espacio de características y el kernel es su producto interno,
$k(x,x')=\phi(x)^\top\phi(x')$; $\gamma>0$ fija el alcance ($\gamma$ grande: solo influyen vecinos muy cercanos) y $K_{ij}=k(x_i,x_j)$ es la matriz de kernels.

**Problema primal (se minimiza):**

$$
\min_{w,b,\xi,\xi^*}\ \tfrac{1}{2}\lVert w\rVert^2 + C\sum_{i=1}^{n}(\xi_i+\xi_i^*)
\quad\text{s.a.}\quad
\begin{cases} y_i - w^\top\phi(x_i) - b \le \varepsilon+\xi_i\\ w^\top\phi(x_i) + b - y_i \le \varepsilon+\xi_i^*\\ \xi_i,\xi_i^*\ge 0\end{cases}
$$

**Problema dual (se maximiza):**

$$
\max_{\alpha,\alpha^*}\ -\tfrac{1}{2}\sum_{i,j}(\alpha_i-\alpha_i^*)(\alpha_j-\alpha_j^*)\,k(x_i,x_j)
-\varepsilon\sum_i(\alpha_i+\alpha_i^*)+\sum_i y_i(\alpha_i-\alpha_i^*),
$$

$$
\text{s.a.}\quad \sum_i(\alpha_i-\alpha_i^*)=0,\qquad 0\le\alpha_i,\alpha_i^*\le C .
$$
''',
    'm5': r'''
Regresión Ridge en el espacio de características del kernel RBF: minimiza el error cuadrático más $\alpha\lVert f\rVert^2$. La solución es densa y exacta,

$$
\hat{c} = (K + \alpha I)^{-1} y, \qquad f(x) = \sum_{i=1}^{n} \hat{c}_i\,k(x_i, x),
$$

donde $K$ es la matriz de kernels entre los estudiantes de entrenamiento. El objetivo se centra dentro de cada ajuste: se resta la media $\bar y$ de las notas de entrenamiento y se suma de nuevo al predecir.

**Notación del kernel.** $k(x,x')=\exp\!\big(-\gamma\lVert x-x'\rVert^2\big)=\phi(x)^\top\phi(x')$, $K_{ij}=k(x_i,x_j)$ y $\mathcal H$ es el espacio de funciones inducido por $k$, con norma $\lVert f\rVert_{\mathcal H}$.

**Problema que se minimiza** (función de pérdida cuadrática más regularización):

$$
\min_{f\in\mathcal H}\ \sum_{i=1}^{n}\big(y_i - f(x_i)\big)^2 + \alpha\,\lVert f\rVert_{\mathcal H}^2
\;=\;\min_{c}\ \lVert y-Kc\rVert^2+\alpha\,c^\top K c,
\qquad f(x)=\sum_i c_i\,k(x_i,x).
$$

**Forma equivalente que se maximiza** (la derivada $y-(K+\alpha I)c=0$ da la solución cerrada de arriba):

$$
\max_{c}\ \ y^\top c-\tfrac{1}{2}\,c^\top (K+\alpha I)\,c .
$$
''',
    'm19': r'''
Resuelve el mismo sistema $(K+\alpha I)c=y$ **sin invertirlo**, con el método de gradiente conjugado truncado (iteración interna de Newton truncado), y el objetivo no se centra. En cada iteración, con residuo $r_t$ y dirección $d_t$,

$$
\eta_t=\frac{r_t^\top r_t}{d_t^\top (K+\alpha I)\,d_t},\qquad
c_{t+1}=c_t+\eta_t d_t,\qquad r_{t+1}=r_t-\eta_t (K+\alpha I)d_t,
$$

$$
d_{t+1}=r_{t+1}+\frac{r_{t+1}^\top r_{t+1}}{r_t^\top r_t}\,d_t .
$$

Se arranca con $c_0=0$ y se detiene antes de converger ($\lVert r_t\rVert\le 0{,}5$, 25 iteraciones sin mejora o 200 como máximo), lo que actúa como regularización implícita.

**Notación del kernel.** Usa el mismo kernel RBF, $k(x,x')=\exp\!\big(-\gamma\lVert x-x'\rVert^2\big)$, y $K_{ij}=k(x_i,x_j)$; $f(x)=\sum_i c_i\,k(x_i,x)$.

**Función que se minimiza** (cuadrática en $c$; su gradiente es $-r=(K+\alpha I)c-y$ y el gradiente conjugado la reduce iterativamente):

$$
\min_{c}\ \ \tfrac{1}{2}\,c^\top (K+\alpha I)\,c-y^\top c
\qquad\Longleftrightarrow\qquad
\max_{c}\ \ y^\top c-\tfrac{1}{2}\,c^\top (K+\alpha I)\,c .
$$

El óptimo es el mismo de Kernel Ridge, $c^{*}=(K+\alpha I)^{-1}y$; aquí se alcanza de forma truncada.
''',
    'm11': r'''
Los pesos se calculan con la densidad estimada (KDE) del objetivo, solo con las notas del entrenamiento de cada ajuste:

$$
w_i = \max\!\big(1 - \alpha\,\hat\phi(y_i),\ \varepsilon\big),
$$

con $\hat\phi$ la densidad normalizada a $[0,1]$ y $\alpha$ (`weight_alpha`) la intensidad. Con $\alpha=0$ todos los pesos son 1 y el modelo equivale a XGBoost sin ponderar. Los pesos entran como `sample_weight` en el objetivo de XGBoost, $\sum_i w_i\,\ell(y_i,\hat y_i)+\sum_k\Omega(f_k)$.
''',
    'm7': r'''
La robustez local de cada estudiante, con objetivo y variables escalados a $[0,1]$, es

$$
r_i = \frac{1}{1 + \max_{j}\ \lvert y_i - y_j\rvert\,/\,(\lVert x_i - x_j\rVert_2 + \epsilon)} .
$$

Las observaciones de menor robustez (la fracción `fraction`) reciben el peso reducido `weight` y el resto peso 1; no se elimina ninguna fila. Con `fraction = 0` o `weight = 1` el modelo equivale a XGBoost sin reponderar.
''',
    'm3': r'''
Conserva el esquema de XGBoost (gradiente $g_i$ y hessiana $h_i$ de segundo orden, con regularización), pero **cada hoja contiene un modelo lineal local (Ridge) en lugar de un valor constante**:

$$
f_k(x) = \beta_{j(x)}^\top\,\tilde{x}\ \ (\text{hoja } j(x)),\qquad
\hat\beta_j=-\Big(\sum_{i\in I_j} h_i\,\tilde x_i\tilde x_i^\top+\lambda I\Big)^{-1}\sum_{i\in I_j} g_i\,\tilde x_i ,
$$

con $\tilde x$ las covariables numéricas más el término constante. El árbol aproxima la función por tramos lineales en vez de por escalones.
''',
    'm14': r'''
Árbol de decisión cuyas divisiones son **conjunciones lógicas** de indicadores binarios (por ejemplo, $z_{\text{programa}}\wedge z_{\text{asignatura}}\wedge\neg z_{\text{cumplimiento}}$), con el modelo lineal de cada hoja sobre las covariables numéricas:

$$
\hat y(x)=\sum_{\ell}\mathbb{1}\big[\,c_\ell(z)=1\,\big]\ \big(\beta_{\ell,0}+\beta_\ell^\top x\big),\qquad c_\ell(z)=\bigwedge_{m} \tilde z_{m}.
$$

Las divisiones se evalúan por razón de verosimilitud y los términos se buscan con recocido simulado adaptativo.
''',
    'm15': r'''
Híbrido de dos etapas. Un proceso gaussiano con kernel $C\cdot(\text{Matérn}_{5/2}+\text{RBF})+\text{White}$ estima la media $\mu(x)$ y la desviación $\sigma(x)$; XGBoost aprende el residuo del GPR:

$$
\hat y(x)=\mu(x)+g\big(x,\ \mu(x),\ \sigma(x)\big),\qquad g\approx y-\mu_{\text{OOF}} ,
$$

donde las meta-variables $\mu_{\text{OOF}}$ y $\sigma_{\text{OOF}}$ de entrenamiento se generan fuera de muestra y agrupadas por estudiante.

**Notación del kernel del GPR**, con $r=\lVert x-x'\rVert$, amplitud $C$ y escalas $\ell_1,\ell_2$:

$$
k(x,x')=C\Big[\sigma_M^2\Big(1+\tfrac{\sqrt5\,r}{\ell_1}+\tfrac{5r^2}{3\ell_1^2}\Big)e^{-\sqrt5\,r/\ell_1}+e^{-r^2/(2\ell_2^2)}\Big]+\sigma_n^2\,\delta_{xx'} .
$$

**Función que se maximiza** (logverosimilitud marginal, con $K_y=K_\theta+\sigma_n^2 I$; cinco reinicios del optimizador):

$$
\max_{\theta}\ \log p(y\mid X,\theta)=-\tfrac12\,y^\top K_y^{-1}y-\tfrac12\log\lvert K_y\rvert-\tfrac n2\log 2\pi ,
$$

y la predicción es $\mu(x_*)=k_*^\top K_y^{-1}y$, $\ \sigma^2(x_*)=k(x_*,x_*)-k_*^\top K_y^{-1}k_*$. La etapa de XGBoost minimiza el objetivo regularizado de su ficha sobre el residuo $y-\mu_{\text{OOF}}$.
''',
    'm16': r'''
Cada registro se convierte en una consulta de texto; un índice **BM25** recupera los $n$ estudiantes más parecidos, con puntaje

$$
\text{BM25}(q,d)=\sum_{t\in q}\text{IDF}(t)\,\frac{f(t,d)\,(k_1+1)}{f(t,d)+k_1\big(1-b+b\,\lvert d\rvert/\overline{\lvert d\rvert}\big)} .
$$

Una red MLP combina las variables del estudiante con las notas de los vecinos recuperados (discretizadas en cuantiles): $\hat y = \text{MLP}\big(x,\ \{y_j\}_{j\in N_n(q)}\big)$, excluyendo al estudiante consultado del conjunto de recuperación.
''',
}


def math_section(key, details_class='details'):
    """Bloque plegable con la notación del modelo, o None si el jbook no lo documenta."""
    text = MATH.get(key)
    if text is None:
        return None
    return html.Details([html.Summary('Notación matemática'),
                         dcc.Markdown(text, mathjax=True, className='prose', link_target='_blank')],
                        className=details_class)
