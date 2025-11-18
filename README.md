# REBCO - AkaiKKR入力ファイル生成ツール

AkaiKKRの入力ファイルを生成・編集するためのPythonツールです。

## 概要

このプロジェクトは、AkaiKKR（第一原理計算コード）の入力ファイルを読み込み、原子の種類を置き換えたり、新しい原子種を定義したりして、複数のバリエーションの入力ファイルを効率的に生成するためのツールです。

## 主な機能

- **入力ファイルの読み込み**: AkaiKKRの入力ファイルを構造化データとして読み込む
- **原子の種類の置換**: 
  - インデックス指定での置換
  - 座標指定での置換
  - ラベル指定での一括置換
- **新しい原子種の定義**: 単一原子種や混合原子種を定義して追加
- **入力ファイルの書き出し**: 構造化データをAkaiKKR入力ファイル形式で書き出し

## ファイル構成

```
REBCO/
├── README.md                 # このファイル（プロジェクト全体の説明）
├── generate_input.py         # メインのモジュール
├── README_generate_input.md  # generate_input.pyの詳細ドキュメント
├── test_generate_input.py    # テストスイート
├── README_test.md            # テストの説明
├── LICENSE                   # ライセンスファイル
└── refs/                     # 参照用の入力ファイル
    └── REBCO/
        └── test-1/
```

## クイックスタート

### 基本的な使用例

```python
from generate_input import (
    load_input_file,
    replace_atom_types_by_label,
    add_atom_type_definition,
    write_input_file,
)

# 入力ファイルを読み込む
input_data = load_input_file("refs/REBCO/test-4/test.in")

# 新しい原子種を定義
new_data = add_atom_type_definition(
    input_data,
    type_name="Fe_new",
    ncmp=1,
    rmt=0.0,
    field=0.0,
    mxl=2,
    atoms=[(26, 100.0)],  # Fe原子100%
)

# ラベル指定で一括置換
modified = replace_atom_types_by_label(
    new_data,
    {"Ba_2t_0": "Fe_new"}
)

# ファイルに書き出し（ディレクトリが存在しない場合は自動作成）
write_input_file(modified, "output/test_modified.in")
```

## ODAT-SEを利用した組成探索

AkaiKKR計算をODAT-SEの探索アルゴリズムに接続して、ハイエントロピー合金 (HEA) の組成を探索するサンプルフローを `optimize_composition.py` / `hea_mapper.toml` に追加しました。

1. `hea_mapper.toml` を編集し、`[[hea.species]]` へ混合したい原子種（原子番号）を列挙します。`akai_command` には AkaiKKR を起動するコマンド列を記述します。使用可能なプレースホルダー:
   - `{input}`: 入力ファイル名（例: `"test.in"`）
   - `{input_path}`: 入力ファイルのフルパス
   - `{output}`: 出力ファイル名（`output_file` 設定で指定、デフォルト: `"test.out"`）
   
   標準入力・標準出力のリダイレクトもサポートされています。推奨設定:
   ```toml
   akai_command = ["specx", "<", "{input}", ">", "{output}"]
   ```
   これは `specx < test.in > test.out` と同等です。`{output}` を省略した場合、標準出力はファイルに保存されません。
2. 動作確認のみを行う場合は `mock_output = "refs/REBCO/test-1/test.out"` を残しておくと、`refs/REBCO/test-1/test.out:523` の `total energy= -59275.587686117` を読み取り、AkaiKKR を実行せずに一連の処理をトレースできます。実際の計算では、`total energy=` と `total energy`（`=`なし）の両方の形式に対応しています。
3. 実計算時は `mock_output` 行を削除し、`output_file` に AkaiKKR が出力するファイル名 (例: `test.out`) を指定して `python optimize_composition.py hea_mapper.toml` を実行します。`target_label`（例: `Y_1h_2`）に対応するサイトへ新しい混合ラベルが適用され、得られた `total energy` が ODAT-SE の目的関数として最小化されます。
4. HEA の各濃度を厳密に 1 へ正規化したい場合は `[hea] simplex_mode = true` を指定してください。この場合、ODAT-SE の `base.dimension` と `algorithm.param.*` は `len([[hea.species]]) - 1` の次元数に合わせます（例: 4 元合金なら 3 次元）。Stick-breaking パラメータ化によって常に非負・総和 1 の組成が生成されます。
5. 最適化したい指標は `[hea.metric]` で選択できます。デフォルトは `total_energy` ですが、`name = "band_energy"` や `pattern = "sigma=..."` のようにカスタム正規表現を指定することで、伝導度など別の観測量にも拡張できます。また、抽出後の値に対して `transform` でメトリクス変換を適用できます（例: `log1p` や `abs`）。

## Appendix: simplex_modeアルゴリズム

`simplex_mode` は ODAT-SE から渡される自由変数を「stick-breaking」変換することで、常に非負かつ総和 1 の濃度ベクトルへ写像します（`optimize_composition.py:243-252`）。

1. 入力次元: 混合する原子種数を `N` とすると、ODAT-SE 側には `N-1` 個の連続変数だけを探索してもらいます（`base.dimension = N-1`）。
2. 変数のクリップ: 各パラメータを `[1e-6, 1-1e-6]` に収め、0 や 1 に張り付いた際の数値不安定を防ぎます。
3. Stick-breaking: 初期残量 `remainder = 1.0` を用意し、各パラメータ `x_i` は「その時点での残量に対する割合」として解釈されます。`portion_i = remainder * x_i` で割り当て、その後 `remainder -= portion_i` と更新します。つまり、各パラメータは「残っている量のうち、どれだけをこの成分に割り当てるか」を表します。
4. 最後の成分: すべての stick を処理したあとに残った `remainder` を `N` 番目の濃度として追加することで、`Σ portion_i + remainder = 1` が常に保証されます。
5. AkaiKKR 入力生成: 得られた濃度ベクトルを `generate_input.py` の `add_atom_type_definition()` / `replace_atom_types_by_label()` に渡し、AkaiKKR の `total energy` を目的関数として返します。

**注意**: 各パラメータは「残量に対する割合」を表すため、全てのパラメータが1に近い値（例: `[1.0, 1.0, 1.0]`）の場合、最初の成分が残量のほぼ100%を占め、残りの成分は非常に小さくなります（例: `[0.999999, 0.000001, 0.0, 0.0]`）。これは「残量の100%を割り当てる」という動作の自然な結果です。均等な組成（例: `[0.25, 0.25, 0.25, 0.25]`）を得たい場合は、パラメータを適切に調整してください（例: 4元合金なら `[0.25, 0.33, 0.5]` 程度）。

この変換により、ODAT-SE は単なる直方体領域を探索するだけで、実際には単体（simplex）上の組成点を評価できるようになります。比例関係にある候補（例: `[0.1,...]` と `[0.2,...]`）が同一になることもありません。

## Appendix: hea.metricによる指標抽出

`optimize_composition.py` では、AkaiKKR の出力ファイルから最小化すべき指標（エネルギーや伝導度など）をパースする `MetricExtractor` を実装しています（`optimize_composition.py:60-93`）。

1. `[hea.metric]` の `name` は、(a) ビルトインパターンを切り替える識別子、(b) ログやエラーメッセージで報告されるラベルの 2 つの意味を持ちます。`pattern` を省略した場合は、`name = "total_energy"` / `"band_energy"` に応じた既定の正規表現が選択され、抽出に成功すると `[Trial ...] ... -> total_energy=...` のように記録されます。既定の `total_energy` パターンは `total energy=` と `total energy`（`=`なし）の両方の形式に対応しています（例: `total energy= -59275.587686117` や `total energy        -64162.390074716`）。
2. 任意の指標を最小化したい場合は `pattern` に正規表現を指定してください。最初に一致したグループの数値を抽出し、`scale` でスカラー倍します（符号反転や単位換算に利用可能）。
3. `ignore_case`（デフォルト: true）を false にすると大文字・小文字を区別した検索になります。`group` で抽出したいキャプチャ番号を指定できます。
4. 抽出結果は `HEAObjective` の `metric.extract()` を通じて取得され、ODAT-SE の目的関数値として返されます。該当行が見つからない場合はエラーになり、設定見直しを促します。

## Appendix: エラーハンドリング

`optimize_composition.py` では、AkaiKKR の計算が失敗した場合や数値が取得できなかった場合に、適切なエラーハンドリングを行います（`optimize_composition.py:165-242`）。

1. **エラー時のペナルティ値**: 計算が失敗した場合、デフォルトで `1.0e10` という大きなペナルティ値を返します。これにより、最適化アルゴリズムは失敗した組成点を避けるようになります。`[hea]` セクションで `error_penalty` を指定することで、この値をカスタマイズできます。

2. **エラーログ**: `[hea]` セクションで `error_log` にファイルパスを指定すると、エラーが発生した試行の詳細情報が記録されます。ログには以下が含まれます：
   - エラーの種類とメッセージ
   - 試行番号と組成パラメータ
   - 入力ファイル、出力ファイル、試行ディレクトリのパス

3. **中間ファイルの保持**: エラーが発生した場合でも、`keep_intermediate = true` が設定されている場合は、失敗した試行のファイルが保持されます。これにより、後でエラーの原因を調査できます。

4. **エラーの種類**: 以下のエラーが捕捉され、ペナルティ値が返されます：
   - `FileNotFoundError`: 出力ファイルが生成されなかった場合
   - `RuntimeError`: AkaiKKR の実行が失敗した場合、または指標が見つからなかった場合
   - `ValueError`: 設定やデータの形式に問題がある場合
   - その他の予期しないエラー

### TOML例（hea.metric）

```toml
[hea.metric]
name = "total_energy"      # 既定のパターンを使用
# name = "band_energy"     # バンドエネルギーを最小化する場合
transform = "identity"     # 取得値への後処理: identity / abs / log / log1p / sqrt / square

# AkaiKKR出力に「sigma = ...」があると仮定して伝導度を最小化する例
# name = "conductivity"
# pattern = "sigma=\\s*([-.0-9Ee]+)"
# scale = 1.0              # 単位換算が必要なら適宜変更
# ignore_case = true
# group = 1

# 例: total_energy を log1p で平滑化
# name = "total_energy"
# transform = "log1p"

# 例: transform のプリセットを増やしたい場合（コード変更が必要）
# - ファイル: optimize_composition.py の MetricExtractor._TRANSFORMS に追記
# - 形式: "cube": lambda x: x ** 3  のように1行追加
# 追加後は TOML で `transform = "cube"` と指定して利用できます。

# spin momentを最小化する例
# name = "spin_moment"
# pattern = "spin moment= ?\\s+([-\\d.+Ee]+)"
# scale = 1.0
# ignore_case = true
# group = 1
```

### TOMLでの設定例

```toml
[base]
dimension = 3  # 4 元合金を探索する場合（= species 数 - 1）

[algorithm]
name = "mapper"

[algorithm.param]
min_list = [0.0, 0.0, 0.0]
max_list = [1.0, 1.0, 1.0]
num_list = [5, 5, 5]

[solver]
name = "function"

[hea]
template_input = "refs/REBCO/test-1/test.in"
target_label = "Y_1h_2"
new_label = "Ln_HEA"
simplex_mode = true  # ← これを有効にすると stick-breaking 変換を使用
error_penalty = 1.0e10  # 計算失敗時のペナルティ値（オプション、デフォルト: 1.0e10）
error_log = "runs/error_log.txt"  # エラーログファイル（オプション）

[hea.metric]
name = "total_energy"  # band_energy / custom pattern
# pattern = "sigma=\\s*([-.0-9Ee]+)"  # 指標がファイル中で別表記の場合は上書き可能

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
```

`simplex_mode = true` を設定すると、ODAT-SE 側で探索する次元は `base.dimension = len([[hea.species]]) - 1` に合わせる必要があります。`algorithm.param` の `min_list` / `max_list` / `num_list` も同じ長さになるよう注意してください。また `[hea.metric]` ブロックでは最小化対象を切り替えられ、`name = "total_energy"` / `"band_energy"` のような既定値に加えて、`pattern = "sigma=\\s*([-.0-9Ee]+)"` のように正規表現を指定することで伝導度など任意のスカラーを抽出できます。

## 詳細ドキュメント

- **`generate_input.py`の詳細**: [README_generate_input.md](README_generate_input.md)
- **テストの説明**: [README_test.md](README_test.md)

## テスト

テストスイートを実行するには：

```bash
python3 test_generate_input.py
```

詳細は [README_test.md](README_test.md) を参照してください。

## ライセンス

MIT License

## 参考資料

- [AkaiKKR公式ドキュメント](https://academeia.github.io/AkaiKKR_Documents/input)
