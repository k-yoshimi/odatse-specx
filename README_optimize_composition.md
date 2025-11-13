# optimize_composition.py パラメータマニュアル

NAME
    optimize_composition.py - AkaiKKRを用いたハイエントロピー合金組成最適化ツール

SYNOPSIS
    python optimize_composition.py <config_file>

DESCRIPTION
    `optimize_composition.py` は、ODAT-SEの探索アルゴリズムとAkaiKKR計算を結合し、
    ハイエントロピー合金（HEA）の組成を自動的に探索するツールです。各候補組成は
    AkaiKKR入力ファイルに変換され、計算が実行された後、出力ファイルから目的指標
    （通常はtotal energy）を抽出してODAT-SEに返します。

    設定はTOML形式のファイルで指定します。以下のセクションで構成されます：

    - [base]          ODAT-SEの基本設定
    - [algorithm]     探索アルゴリズムの設定
    - [algorithm.param] アルゴリズムパラメータ
    - [solver]       ソルバー設定
    - [runner]       ランナー設定
    - [hea]          HEA最適化の主要設定
    - [hea.metric]   指標抽出設定
    - [[hea.species]] 原子種の定義（配列）

CONFIGURATION SECTIONS

[base]
    基本設定セクション。ODAT-SEの基本パラメータを指定します。

    dimension (integer, required)
        探索空間の次元数。simplex_modeが有効な場合、原子種数-1に設定します。
        例: 4元合金でsimplex_mode=trueの場合、dimension=3

    root_dir (string, optional, default: ".")
        作業ディレクトリのルートパス。相対パスはこのディレクトリを基準に解決されます。

    output_dir (string, optional, default: "odatse/output")
        ODAT-SEの出力ディレクトリ。

[algorithm]
    探索アルゴリズムの設定セクション。

    name (string, required)
        使用するアルゴリズム名。例: "mapper" など。

    seed (integer, optional)
        乱数シード。再現性のある結果を得るために指定します。

    colormap (string, optional)
        カラーマップファイルのパス。

[algorithm.param]
    アルゴリズム固有のパラメータセクション。

    min_list (array of floats, required)
        各次元の下限値のリスト。長さはdimensionと一致する必要があります。
        例: [0.0, 0.0, 0.0]

    max_list (array of floats, required)
        各次元の上限値のリスト。長さはdimensionと一致する必要があります。
        例: [1.0, 1.0, 1.0]

    num_list (array of integers, required)
        各次元のグリッド点数（mapperアルゴリズムの場合）。
        例: [5, 5, 5]

[solver]
    ソルバー設定セクション。

    name (string, required)
        ソルバー名。 "function" を指定します。

[runner]
    ランナー設定セクション。

    [runner.log]
        ログ設定のサブセクション。

        interval (integer, optional, default: 10)
            ログ出力間隔（試行数）。

[hea]
    HEA最適化の主要設定セクション。このセクションは必須です。

    template_input (string, required)
        AkaiKKR入力ファイルのテンプレートパス。このファイルを読み込み、
        指定された原子種ラベルを混合原子種に置き換えます。

    target_label (string, required)
        置き換え対象の原子種ラベル。このラベルを持つ原子種が混合原子種に
        置き換えられます。例: "Y_1h_2"

    new_label (string, optional, default: "{target_label}_mix")
        新しく作成する混合原子種のラベル名。例: "Ln_HEA"

    work_dir (string, optional, default: "runs")
        各試行の作業ディレクトリのベースパス。各試行は
        {work_dir}/trial_{試行番号:05d} に作成されます。

    output_file (string, optional, default: "test.out")
        AkaiKKRが生成する出力ファイル名。このファイルから指標を抽出します。

    akai_command (array of strings or string, required)
        AkaiKKRを実行するコマンド。配列形式または文字列形式で指定できます。
        プレースホルダーとして以下が使用可能です：
        - {input}     入力ファイル名のみ（例: "test.in"）
        - {input_path} 入力ファイルのフルパス

        例:
          akai_command = ["akaiKKR", "{input}"]
          akai_command = ["/usr/local/bin/akaiKKR", "-option", "{input_path}"]

    keep_intermediate (boolean, optional, default: false)
        trueに設定すると、各試行の作業ディレクトリを保持します。
        falseの場合、成功した試行のディレクトリは削除されます。
        エラーが発生した場合でも、この設定に従ってファイルが保持/削除されます。

    mock_output (string, optional)
        動作確認用のモック出力ファイルパス。指定すると、AkaiKKRを実行せずに
        このファイルをコピーして使用します。実計算時はこの行を削除してください。

    simplex_mode (boolean, optional, default: false)
        trueに設定すると、stick-breaking変換を使用して、常に総和が1.0になる
        組成を生成します。この場合、base.dimensionは原子種数-1に設定する必要があります。

    error_penalty (float, optional, default: 1.0e10)
        計算が失敗した場合に返すペナルティ値。最適化アルゴリズムが失敗した
        組成点を避けるために使用されます。

    error_log (string, optional)
        エラーログファイルのパス。指定すると、エラーが発生した試行の詳細情報が
        記録されます。ログには以下が含まれます：
        - エラーの種類とメッセージ
        - 試行番号と組成パラメータ
        - 入力ファイル、出力ファイル、試行ディレクトリのパス

    timeout_sec (integer, optional)
        AkaiKKR実行のタイムアウト時間（秒）。指定しない場合、タイムアウトは
        適用されません。

    env (dictionary, optional)
        AkaiKKR実行時に設定する環境変数の辞書。例:
          env = { "OMP_NUM_THREADS" = "4" }

    rmt (float, optional)
        混合原子種のMT半径。指定しない場合、target_labelの原子種のrmt値が
        使用されます。

    field (float, optional)
        混合原子種の磁場。指定しない場合、target_labelの原子種のfield値が
        使用されます。

    mxl (integer, optional)
        混合原子種の最大角運動量。指定しない場合、target_labelの原子種の
        mxl値が使用されます。

[hea.metric]
    指標抽出設定セクション。AkaiKKR出力ファイルから目的指標を抽出する方法を
    指定します。

    name (string, optional, default: "total_energy")
        指標名。以下のビルトインパターンが利用可能です：
        - "total_energy"  total energyを抽出（デフォルト）
        - "band_energy"   band energyを抽出

        カスタム指標を使用する場合は、patternも指定してください。

    pattern (string, optional)
        指標を抽出するための正規表現パターン。nameで指定したビルトインパターンが
        使用できない場合、またはカスタムパターンを使用する場合に指定します。

        例:
          pattern = "sigma=\\s*([-.0-9Ee]+)"  # 伝導度を抽出

    group (integer, optional, default: 1)
        正規表現のキャプチャグループ番号。抽出したい数値が含まれるグループを
        指定します。

    scale (float, optional, default: 1.0)
        抽出した値に掛けるスカラー値。単位換算や符号反転に使用します。

    ignore_case (boolean, optional, default: true)
        trueの場合、大文字小文字を区別せずに検索します。

[[hea.species]]
    原子種定義の配列セクション。混合する各原子種を定義します。少なくとも1つ、
    simplex_modeが有効な場合は少なくとも2つのエントリが必要です。

    label (string, required)
        原子種のラベル名。例: "Y", "La", "Nd"

    atomic_number (integer, required)
        原子番号。例: 39 (Y), 57 (La), 60 (Nd)

    symbol (string, optional)
        labelの代替指定。labelが指定されていない場合に使用されます。

EXAMPLES

基本的な4元合金の組成探索:

    [base]
    dimension = 3
    root_dir = "."
    output_dir = "odatse/output"

    [algorithm]
    name = "mapper"
    seed = 20240502

    [algorithm.param]
    min_list = [0.0, 0.0, 0.0]
    max_list = [1.0, 1.0, 1.0]
    num_list = [5, 5, 5]

    [solver]
    name = "function"

    [runner]
    [runner.log]
    interval = 10

    [hea]
    template_input = "refs/REBCO/test-1/test.in"
    target_label = "Y_1h_2"
    new_label = "Ln_HEA"
    work_dir = "runs/hea_trials"
    output_file = "test.out"
    akai_command = ["akaiKKR", "{input}"]
    keep_intermediate = false
    simplex_mode = true
    error_penalty = 1.0e10
    error_log = "runs/error_log.txt"

    [hea.metric]
    name = "total_energy"

    [[hea.species]]
    label = "Y"
    atomic_number = 39

    [[hea.species]]
    label = "La"
    atomic_number = 57

    [[hea.species]]
    label = "Nd"
    atomic_number = 60

    [[hea.species]]
    label = "Sm"
    atomic_number = 62

カスタム指標（伝導度）を最小化する例:

    [hea.metric]
    name = "conductivity"
    pattern = "sigma=\\s*([-.0-9Ee]+)"
    scale = 1.0
    ignore_case = true
    group = 1

環境変数を設定してAkaiKKRを実行する例:

    [hea]
    akai_command = ["/usr/local/bin/akaiKKR", "{input}"]
    env = { "OMP_NUM_THREADS" = "4", "MKL_NUM_THREADS" = "4" }
    timeout_sec = 3600

NOTES

次元数の設定:
    simplex_modeが有効な場合、base.dimensionは原子種数-1に設定する必要があります。
    例: 4元合金の場合、dimension=3

    simplex_modeが無効な場合、base.dimensionは原子種数に設定します。
    例: 4元合金の場合、dimension=4

stick-breaking変換:
    simplex_modeが有効な場合、ODAT-SEから渡されるN-1個のパラメータが
    stick-breaking変換により、常に総和が1.0になるN個の濃度に変換されます。
    これにより、組成の制約が自動的に満たされます。

エラーハンドリング:
    計算が失敗した場合、error_penaltyで指定した値（デフォルト: 1.0e10）が
    返されます。これにより、最適化アルゴリズムは失敗した組成点を避けるよう
    になります。error_logが指定されている場合、エラーの詳細が記録されます。

SEE ALSO
    README.md
    README_generate_input.md
    hea_mapper.toml

