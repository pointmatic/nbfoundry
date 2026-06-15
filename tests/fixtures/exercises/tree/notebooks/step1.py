# Copyright (c) 2026 Pointmatic
# SPDX-License-Identifier: Apache-2.0
import marimo

app = marimo.App()


@app.cell
def _():
    data = [1, 2, 3]
    return (data,)


if __name__ == "__main__":
    app.run()
