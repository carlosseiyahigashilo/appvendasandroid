from kivy.app import App
from kivy.lang import Builder
from telas import *
from botoes import *
import requests
from bannervenda import BannerVenda
from bannervendedor import BannerVendedor
import os
from functools import partial
from myfirebase import MyFirebase
from datetime import date

GUI = Builder.load_file('main.kv')

class MainApp(App):
    cliente = None
    produto = None
    unidade = None

    def build(self):
        self.firebase = MyFirebase()
        return GUI
    
    def on_start(self): 
        # carregar as fotos de perfil
        pagina_fotoperfilpage = self.root.ids['fotoperfilpage']
        lista_fotos = pagina_fotoperfilpage.ids['lista_fotos_perfil']
        fotos = os.listdir('icones/fotos_perfil')
        for foto in fotos:
            if 'hash' not in foto:
                imagem = ImageButton(source=f"icones/fotos_perfil/{foto}", on_release=partial(self.mudar_foto_perfil, foto))
                lista_fotos.add_widget(imagem)
        
        # carregar as fotos dos clientes
        pagina_adicionarvendas = self.root.ids['adicionarvendaspage']
        lista_clientes = pagina_adicionarvendas.ids['lista_clientes']
        clientes = os.listdir('icones/fotos_clientes')
        for cliente in clientes:
            imagem = ImageButton(source=f'icones/fotos_clientes/{cliente}', on_release = partial(self.selecionar_cliente, cliente))
            label = LabelButton(text=cliente.replace('.png', '').capitalize(), on_release = partial(self.selecionar_cliente, cliente))
            lista_clientes.add_widget(imagem)
            lista_clientes.add_widget(label)

        # carregar as fotos dos produtos
        lista_produtos = pagina_adicionarvendas.ids['lista_produtos']
        produtos = os.listdir('icones/fotos_produtos')
        for produto in produtos:
            imagem = ImageButton(source=f'icones/fotos_produtos/{produto}', on_release = partial(self.selecionar_produto, produto))
            label = LabelButton(text=produto.replace('.png', '').capitalize(), on_release = partial(self.selecionar_produto, produto))
            lista_produtos.add_widget(imagem)
            lista_produtos.add_widget(label)
        
        # carregar a data
        pagina_adicionarvendas = self.root.ids['adicionarvendaspage']
        label_data = pagina_adicionarvendas.ids['label_data']
        label_data.text = f'Data: {date.today().strftime("%d/%m/%Y")}'

        # carregas as infos do usuário
        self.carregar_infos_usuario()

    # informações que dependem do usuário
    def carregar_infos_usuario(self):
        try:
            with open('refreshtoken.txt', 'r') as arquivo:
                refresh_token = arquivo.read()
            local_id, id_token = self.firebase.trocar_token(refresh_token)
            self.local_id = local_id
            self.id_token = id_token

            # pegar informações do usuário
            requisicao = requests.get(f'https://aplicativovendashash-8dd84-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}')
            requisicao_dic = requisicao.json()

            # preencher foto de perfil
            avatar = requisicao_dic['avatar']
            self.avatar = avatar
            foto_perfil = self.root.ids['foto_perfil']
            foto_perfil.source = f"icones/fotos_perfil/{avatar}"

            # preencher o total de vendas
            total_vendas = float(requisicao_dic['total_vendas'])
            self.total_vendas = total_vendas
            homepage = self.root.ids['homepage']
            homepage.ids['label_total_vendas'].text = f'[color=#000000]Total de Vendas:[/color] [b]R${total_vendas:.1f}[/b]'

            # preencher o ID único
            id_vendedor = requisicao_dic['id_vendedor']
            self.id_vendedor = id_vendedor
            pagina_ajustes = self.root.ids['ajustespage']
            pagina_ajustes.ids['id_vendedor'].text = f'Seu ID Único: {id_vendedor}'

            # preencher equipe
            self.equipe = requisicao_dic['equipe']

            # preencher lista de vendas
            try:  
                vendas = requisicao_dic['vendas']
                self.vendas = vendas
                pagina_homepage = self.root.ids['homepage']
                lista_vendas = pagina_homepage.ids['lista_vendas']
                for id_venda in vendas:
                    venda = vendas[id_venda]
                    banner = BannerVenda(cliente=venda['cliente'], foto_cliente=venda['foto_cliente'],\
                                        produto=venda['produto'], foto_produto=venda['foto_produto'],\
                                        data=venda['data'], preco=venda['preco'], unidade=venda['unidade'],\
                                        quantidade=venda['quantidade'])
                    lista_vendas.add_widget(banner)
            except Exception as excecao:
                print(excecao)
            
            # preencher equipe de vendedores
            equipe = requisicao_dic['equipe']
            lista_equipe = equipe.split(',')
            pagina_listavendedores = self.root.ids['listarvendedorespage']
            lista_vendedores = pagina_listavendedores.ids['lista_vendedores']
            for id_vendedor_equipe in lista_equipe:
                if id_vendedor != '':
                    banner_vendedor = BannerVendedor(id_vendedor=id_vendedor_equipe)
                    lista_vendedores.add_widget(banner_vendedor)

            self.mudar_tela('homepage')
        except:
            pass

    def mudar_tela(self, id_tela):
        gerenciador_telas = self.root.ids['screen_manager']
        gerenciador_telas.current = id_tela

    def mudar_foto_perfil(self, foto, *args):
        foto_perfil = self.root.ids['foto_perfil']
        foto_perfil.source = f'icones/fotos_perfil/{foto}'
        info = f'{{"avatar": "{foto}"}}'
        requisicao = requests.patch(f'https://aplicativovendashash-8dd84-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}',\
                                    data=info)
        self.mudar_tela('ajustespage')
    
    def adicionar_vendedor(self, id_vendedor_adicionado):
        link = f'https://aplicativovendashash-8dd84-default-rtdb.firebaseio.com/.json?orderBy="id_vendedor"&equalTo="{id_vendedor_adicionado}"'
        requisicao = requests.get(link)
        requisicao_dic = requisicao.json()
        pagina_adicionarvendedor = self.root.ids['adicionarvendedorpage']
        mensagem_texto = pagina_adicionarvendedor.ids['mensagem_outrovendedor']

        if requisicao_dic == {}:
            mensagem_texto.text = 'Usuário Não Encontrado'
        else:
            equipe = self.equipe.split(',')
            if id_vendedor_adicionado in equipe:
                mensagem_texto.text = 'Vendedor já faz parte da equipe'
            else:
                self.equipe = self.equipe + f",{id_vendedor_adicionado}"
                info = f'{{"equipe": "{self.equipe}"}}'
                requests.patch(f'https://aplicativovendashash-8dd84-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}', data=info)
                mensagem_texto.text = 'Vendedor adicionado com sucesso'
                # adicionar um novo banner na lista de vendedores
                pagina_listavendedores = self.root.ids['listarvendedorespage']
                lista_vendedores= pagina_listavendedores.ids['lista_vendedores']
                banner_vendedor = BannerVendedor(id_vendedor=id_vendedor_adicionado)
                lista_vendedores.add_widget(banner_vendedor)
    
    def selecionar_cliente(self, cliente, *args):
        self.cliente = cliente.replace('.png', '')
        # pintar de branco todas as outras letras
        pagina_adicionarvendas = self.root.ids['adicionarvendaspage']
        lista_clientes = pagina_adicionarvendas.ids['lista_clientes']
        for item in list(lista_clientes.children):
            item.color = (1, 1, 1, 1)
            # pintar de azul a letra do item que selecionamos
            try:
                texto = item.text.lower() + '.png'
                if cliente == texto:
                    item.color = (0, 207/255, 219/255, 1)
            except:
                pass
    
    def selecionar_produto(self, produto, *args):
        self.produto = produto.replace('.png', '')
        pagina_adicionarvendas = self.root.ids['adicionarvendaspage']
        lista_produtos = pagina_adicionarvendas.ids['lista_produtos']
        for item in list(lista_produtos.children):
            item.color = (1, 1, 1, 1)
            try:
                texto = item.text.lower() + '.png'
                if produto == texto:
                    item.color = (0, 207/255, 219/255, 1)
            except Exception as excecao:
                print('Erro na função selecionar_produto(): ', excecao)
    
    def selecionar_unidade(self, id_label, *args):
        self.unidade = id_label.replace('unidades_', '')
        pagina_adicionarvendas = self.root.ids['adicionarvendaspage']
        # pintar todo mundo de branco
        pagina_adicionarvendas.ids['unidades_kg'].color = (1, 1, 1, 1)
        pagina_adicionarvendas.ids['unidades_unidades'].color = (1, 1, 1, 1)
        pagina_adicionarvendas.ids['unidades_litros'].color = (1, 1, 1, 1)

        # pintar o cara selecionado de azul
        pagina_adicionarvendas.ids[id_label].color = (0, 207/255, 219/255, 1)
    
    def adicionar_venda(self):
        cliente = self.cliente
        produto = self.produto
        unidade = self.unidade
        pagina_adicionarvendas = self.root.ids['adicionarvendaspage']
        data = pagina_adicionarvendas.ids['label_data'].text.replace('Data: ', '')
        preco = pagina_adicionarvendas.ids['preco_total'].text
        quantidade = pagina_adicionarvendas.ids['quantidade'].text

        if not cliente:
            pagina_adicionarvendas.ids['label_selecione_cliente'].color = (1, 0, 0, 1)
        if not produto:
            pagina_adicionarvendas.ids['label_selecione_produto'].color = (1, 0, 0, 1)
        if not unidade:
            pagina_adicionarvendas.ids['unidades_kg'].color = (1, 0, 0, 1)
            pagina_adicionarvendas.ids['unidades_unidades'].color = (1, 0, 0, 1)
            pagina_adicionarvendas.ids['unidades_litros'].color = (1, 0, 0, 1)
        if not preco:
            pagina_adicionarvendas.ids['label_preco'].color = (1, 0, 0, 1)
        else:
            try:
                preco = float(preco)
            except:
                pagina_adicionarvendas.ids['label_preco'].color = (1, 0, 0, 1)
        if not quantidade:
            pagina_adicionarvendas.ids['label_quantidade'].color = (1, 0, 0, 1)
        else:
            try:
                quantidade = float(quantidade)
            except:
                pagina_adicionarvendas.ids['label_quantidade'].color = (1, 0, 0, 1)
        
        # dado que ele preencheu tudo, vamos executar o código de adicionar_venda
        if cliente and produto and unidade and preco and quantidade and (type(preco) == float) and (type(quantidade) == float):
            foto_cliente = cliente + '.png'
            foto_produto = produto + '.png'

            info = f'{{"cliente": "{cliente}", "produto": "{produto}", "foto_cliente": "{foto_cliente}", ' \
            f'"foto_produto": "{foto_produto}", "data": "{data}", "preco": "{preco}", ' \
            f'"unidade": "{unidade}", "quantidade": "{quantidade}"}}'
            requests.post(f'https://aplicativovendashash-8dd84-default-rtdb.firebaseio.com/{self.local_id}/vendas.json?auth={self.id_token}',
                          data=info)
            banner = BannerVenda(cliente=cliente, produto=produto, foto_cliente=foto_cliente,
                                 foto_produto=foto_produto, data=data, preco=preco, quantidade=quantidade, unidade=unidade)
            pagina_homepage = self.root.ids['homepage']
            lista_vendas = pagina_homepage.ids['lista_vendas']
            lista_vendas.add_widget(banner)

            requisicao = requests.get(f'https://aplicativovendashash-8dd84-default-rtdb.firebaseio.com/{self.local_id}/total_vendas.json?auth={self.id_token}')
            total_vendas = float(requisicao.json())
            total_vendas += preco
            info = f'{{"total_vendas": "{total_vendas}"}}'
            requests.patch(f'https://aplicativovendashash-8dd84-default-rtdb.firebaseio.com/{self.local_id}.json?auth={self.id_token}',
                           data=info)
            pagina_homepage.ids['label_total_vendas'].text = f'[color=#000000] Total Vendas:[/color] [b]R${total_vendas}[/b]'

            self.mudar_tela('homepage')
        self.cliente = None
        self.produto = None
        self.unidade = None
    
    def carregar_todas_vendas(self):
        pagina_todasvendaspage = self.root.ids['todasvendaspage']
        lista_vendas = pagina_todasvendaspage.ids['lista_vendas']

        for item in list(lista_vendas.children):
            lista_vendas.remove_widget(item)
        # preencher a página todasvendaspage
        # pegar informações da empresa
        requisicao = requests.get(f'https://aplicativovendashash-8dd84-default-rtdb.firebaseio.com/.json?orderBy="id_vendedor"')
        requisicao_dic = requisicao.json()

        # preencher foto de perfil da empresa
        foto_perfil = self.root.ids['foto_perfil']
        foto_perfil.source = 'icones/fotos_perfil/hash.png'

        # preencher lista de vendas da empresa
        total_vendas = 0
        for local_id_usuario in requisicao_dic:
            try:
                vendas = requisicao_dic[local_id_usuario]['vendas']
                for id_venda in vendas:
                    venda = vendas[id_venda]
                    total_vendas += float(venda['preco'])
                    banner = BannerVenda(cliente=venda['cliente'], foto_cliente=venda['foto_cliente'],
                                     produto=venda['produto'], foto_produto=venda['foto_produto'],
                                     quantidade=venda['quantidade'], unidade=venda['unidade'],
                                     preco=venda['preco'], data=venda['data'])
                    lista_vendas.add_widget(banner)
            except Exception as excecao:
                print('Erro na funcao carregar_todas_vendas: ', excecao)

        # preencher o total de vendas
        pagina_todasvendaspage.ids['label_total_vendas'].text = f'[color=#000000]R$Total Vendas:[/color] [b]R${total_vendas}[/b]'

        # redirecionar pra página todasvendaspage
        self.mudar_tela('todasvendaspage')

    def sair_todas_vendas(self, id_tela):
        foto_perfil = self.root.ids['foto_perfil']
        foto_perfil.source = f'icones/fotos_perfil/{self.avatar}'
        self.mudar_tela(id_tela)
    
    def carregar_vendas_vendedor(self, dic_info_vendedor, *args):
        try:
            pagina_vendasoutrovendedor = self.root.ids['vendasoutrovendedorpage']
            lista_vendas = pagina_vendasoutrovendedor.ids['lista_vendas']
            # limpar vendas anteriores
            for item in list(lista_vendas.children):
                lista_vendas.remove_widget(item)
            vendas = dic_info_vendedor['vendas']
            for id_venda in vendas:
                venda = vendas[id_venda]
                banner = BannerVenda(cliente=venda['cliente'], produto=venda['produto'], foto_cliente=venda['foto_cliente'],
                                     foto_produto=venda['foto_produto'], data=venda['data'], quantidade=venda['quantidade'],
                                     preco=venda['preco'], unidade=venda['unidade'])
                lista_vendas.add_widget(banner)
        except Exception as e:
            print(e)
        # preencher o total de vendas
        total_vendas = dic_info_vendedor['total_vendas']
        pagina_vendasoutrovendedor.ids['label_total_vendas'].text = f'[color=#000000]Total Vendas: [/color] [b]R${total_vendas}[/b]'

        # preencher a foto de perfil
        avatar = dic_info_vendedor['avatar']
        foto_perfil = self.root.ids['foto_perfil']
        foto_perfil.source = f'icones/fotos_perfil/{avatar}'

        self.mudar_tela('vendasoutrovendedorpage')
        
MainApp().run()