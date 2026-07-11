from flask import jsonify, request

from models import produto_model


def listar():
    produtos = produto_model.get_todos()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_por_id(id):
    produto = produto_model.get_por_id(id)
    if produto:
        return jsonify({"dados": produto, "sucesso": True}), 200
    return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404


def criar():
    dados = request.get_json()
    erro = produto_model.validar_produto(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    id = produto_model.criar(
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    return jsonify({"dados": {"id": id}, "sucesso": True, "mensagem": "Produto criado"}), 201


def atualizar(id):
    dados = request.get_json()

    produto_existente = produto_model.get_por_id(id)
    if not produto_existente:
        return jsonify({"erro": "Produto não encontrado"}), 404

    erro = produto_model.validar_produto(dados)
    if erro:
        return jsonify({"erro": erro}), 400

    produto_model.atualizar(
        id,
        dados["nome"],
        dados.get("descricao", ""),
        dados["preco"],
        dados["estoque"],
        dados.get("categoria", "geral"),
    )
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar(id):
    produto = produto_model.get_por_id(id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404

    produto_model.deletar(id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min = request.args.get("preco_min", None)
    preco_max = request.args.get("preco_max", None)

    if preco_min:
        preco_min = float(preco_min)
    if preco_max:
        preco_max = float(preco_max)

    resultados = produto_model.buscar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
