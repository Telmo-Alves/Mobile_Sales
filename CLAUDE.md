# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask-based mobile sales application that connects to a Firebird database (gescom_risatel) for a retail/inventory management system. The application provides a web interface for managing clients, products, orders, and inventory.

## Architecture

### Core Components
- **app.py**: Main Flask application with all routes and business logic
- **config.py**: Database and application configuration
- **templates/**: Jinja2 HTML templates using Bootstrap for UI
- **static/css/**: Custom CSS styling

### Database
- Firebird SQL database (gescom_risatel) accessed via `fdb` library
- Connection parameters defined in `config.py`
- Main tables: Artigos, Utiliza_Web, Clientes, Stock_Lotes, Lotes, Ficha_Lab_Lote

### Authentication
- Custom session-based authentication using Utiliza_Web table
- Users login with numeric IDs (01, 02, etc) that get prefixed with 'U' internally
- Access levels determined by vendedor field (INTEGER)

## Development Commands

### Running the Application
```bash
# Development server
python app.py

# Production with Gunicorn
gunicorn --bind 0.0.0.0:5000 app:app

# Test database connection
python test_connection.py
```

### Virtual Environment
```bash
# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Key Routes and Features

- `/login` - User authentication (U01, U02, etc)
- `/dashboard` - Main dashboard with alerts and stats
- `/existencias` - Inventory search and stock checking
- `/clientes` - Client management
- `/artigos` - Product management
- `/pedidos` - Order management
- `/estatisticas` - Sales statistics

## Important Notes

- Session timeout set to 8 hours
- Character encoding: WIN1252 (legacy Windows encoding from Firebird)
- Vendedor field is INTEGER in database, not string
- Access levels: vendedor 1,2 = level 1; vendedor 20 = level 2; vendedor 99 = level 3
- Stock queries join Stock_Lotes with Lotes table for batch tracking
- Lab results available for certain products via Ficha_Lab_Lote table
- reinicia sempre o apache2.service
- analisa este codigo legado : <?php
  session_start();

  include("private/vars.php");
  include("private/validar.php");
?>

<html>

<FORM>
  <head>
    <title>Listagem de Existencias por Lote</title>
  </head>

  <BODY bgcolor="#ffffff" text="black"><font face="arial,verdana,helvetica" size=3>
<meta name="viewport" content="width=240">
<?php


$_SESSION["codigo"] = $_GET["Codigo"];

echo "<INPUT TYPE=Button style=\"width: 70;font-size: 10pt\" VALUE=\"Menu\" onclick=\"location.href='menu.php'\">";
echo "<INPUT TYPE=\"button\" style=\"width: 70;font-size: 10pt\" VALUE=\"Cliente\" onclick=\"location.href='mapaenccli.php'\">";
echo "<INPUT TYPE=\"button\" style=\"width: 70;font-size: 10pt\" VALUE=\"Fornecedor\" onclick=\"location.href='mapaencforn.php'\">";

$X_Codigo    = $_GET["Codigo"];
$X_Descricao = $_GET["Descricao"];
//echo $X_Descricao;

//$X_EncForn   = $_POST["encforn"];
$StkMinimo   = 20;

//echo "<BR>encforn : ".$_POST["encforn"];
//echo "<BR>encforn : ".$_GET["encforn"];

echo "<BR> <a style=\"font-weight:bold;font-size: 10pt;color: red\"\a><BR>".SubStr( $X_Descricao, 0, 55)."<BR><BR>";

$_SESSION["xcodigo"]   = $X_Codigo;
$_SESSION["descricao"] = $X_Descricao;


$C_Codigo       =  0;
$C_Lote         =  1;
$C_LoteForn     =  2;
$C_QtExist      =  3;
$C_QtDisp       =  4;
$C_QtReserv     =  5;
$C_Fornecedor   =  6;
$C_NomeForn     =  7;
$C_Descricao    =  8;
$C_Restricao    =  9;
$C_Preco        = 10;
$C_Preco2       = 11;
$C_PCompra      = 12;
$C_Moeda        = 13;
$C_CdEntrega    = 14;
$C_Chave        = 15;
$C_TipoNivel    = 16;
$C_Nivel        = 17;
$C_Preco3       = 18;
$C_Preco4       = 19;
$C_Codigo_Cor   = 21;
$C_Armazem      = 22;
$C_PCusto       = 23;
$C_Sigla        = 24;
$C_Fixacao      = 25;
$Forma_Pag_Desc = 26;
$Prazo_NDias    = 27;
$StkMinimo      = 0;

$nivel = 0;

if ( ( $_SESSION["cd_vend"] == 1 ) Or ( $_SESSION["cd_vend"] == 2 ) ) { $nivel = 1; };
if ( ( $_SESSION["cd_vend"] == 20 ) Or ( $_SESSION["cd_vend"] == 99 ) ) { $nivel = 99; };



echo "<table border='1'";
echo "<thead>";

//echo "<col width=100>";

$letra     = "10pt";
$altura    = "20";
echo "<tr>";
echo "<th nowrap style=\"font-size: \"".$letra."\" align=center width=061 >Exist&ecirc;ncia</th>";
echo "<th nowrap style=\"font-size: \"".$letra."\" align=center width=061 >Reservado</th>";
echo "<th nowrap style=\"font-size: \"".$letra."\" align=center width=064 >Dispon&igrave;vel</th>";
echo "<th nowrap style=\"font-size: \"".$letra."\" align=center width=240 >Resultados Laboratoriais</th>";
//echo "<td height=\"20\" nowrap style=\"font-size: 10pt\" align=center width=080 >ResLab</td>";
echo "<th nowrap style=\"font-size: \"".$letra."\" align=center width=050 >Situa&ccedil;&atilde;o</th>";
if ( $nivel > 0 ) 
{
  echo "<th nowrap style=\"font-size: \"".$letra."\" align=center width=100 >Fornecedor</th>";
}
echo "<th nowrap style=\"font-size: \"".$letra."\" align=center width=080 >Lote</th>";
//echo "<td nowrap style=\"font-size: 10pt\" align=center width=080 >Descricao</td>";
echo "<th nowrap style=\"font-size: \"".$letra."\" align=center width=035 ><b>PV</b></th>";
echo "<th nowrap style=\"font-size: \"".$letra."\" align=center width=035 >PV I</th>";
if ( $nivel > 0 ) 
{
  echo "<th nowrap style=\"font-size: \"".$letra."\" align=center width=35 ><b>Custo</th>";
}
//echo "<td nowrap style=\"font-size: 10pt\" align=center width=025 >Ar</td>";
if ( $nivel == 99 ) 
{
  echo "<th nowrap style=\"font-size: \"".$letra."\" align=center width=150 >Compra</th>";
}
//echo "<td nowrap style=\"font-size: 10pt\" align=center width=035 >SITUA</td>";

echo "</tr>";
echo "</thead>";

$salto = "<BR>";

  // Set Database Access Info

$PMC = 0;
$PMC_Qt = 0;
$PMC_Exist = 0;

$PMC2 = 0;
$PMC_Qt2 = 0;
$PMC_Exist2 = 0;

$db_handle = ibase_connect ($db_host, $db_username, $db_password );
$sql_users = "Select RCodigo, RLote, RLoteFor, RExist, (RExist - REncCli + REncFor) as RStkDisp,"
             ." REncCli, RFornec, RNomeFor, RDescricao, RTipoSitua, RPvp1, RPvp2, RPreco_UN, RMoeda,"
             ." RCond_Entrega, RChave, RTipoNivel, RNivel, RPvp3, RPvp4, RTipoSituaDesc, RCodigo_Cor,"
             ." RArmazem, RPreco_Compra, RSigla, RFixacao, RForma_Pag_Desc, RPrazo_NDias From Inq_Exist_Lote_Pda_2('".$X_Codigo."', '"
             .$X_Codigo."', ".$arm_ini.", ".$arm_fim.", 'ACT', 0, '31.12.3000', '".$_SESSION["encforn"]."', '31.12.3000', 0, 'S', 1, 2, 2)"
             ." Order By RChave ASC, RExist ASC, ROrdem";
$query_users = ibase_query ($db_handle, $sql_users);
//echo "query principal : ".$sql_users;
while ($row = ibase_fetch_row ($query_users))
{

// Obter resultados laboratorio
$Ne_Valor             = 00;
$Ne_Cv                = 1;
$Uster_CVM            = 2;
$Uster_PNTFinos       = 3;
$Uster_PNTGrossos     = 4;
$Uster_Neps2          = 5;
$Rkm_Valor            = 6;
$Rkm_Cv               = 7;
$Rkm_Along_Valor      = 8;
$Rkm_Along_Cv         = 9;
$Tipo_Torcao          = 10;
$Torcao_TPI_Valor     = 11;
$Tipo_Torcao_S        = 12;
$Torcao_TPI_Valor_S   = 13;
$Nr_Fios              = 14;
$Uster_Pilosidade     = 15;
$Uster_Pilosidade_Cvb = 16;
$Uster_Neps3          = 17;
$Tipo_Processo        = 18;


$db_handle2 = ibase_pconnect ($db_host, $db_username, $db_password);
$sql_users2 = "Select First 1 L.Ne_Valor, L.Ne_Cv, L.Uster_CVM, L.Uster_PNTFinos2, L.Uster_PNTGrossos2, L.Uster_Neps_2, "
            ."L.Rkm_Valor, L.Rkm_Cv, L.Rkm_Along_Valor, L.Rkm_Along_Cv, L.Tipo_Torcao, L.Torcao_TPI_Valor, L.Tipo_Torcao_S,"
            ." L.Torcao_TPI_Valor_S, T.Nr_Fios, L.Uster_Pilosidade, L.Uster_Pilosidade_Cv, L.Uster_Neps_3, L.Tipo_Processo "
            ."From Ficha_Lab_Lote L Left Outer Join Tipo_Torcedura T ON "
            ."T.Tipo = L.Tipo_Torcedura Where Codigo = '".$row[ 0 ]."' And Lote = '".$row[ 1 ]."' order by L.nr_relatorio DESC";
$Resultados = "";
//echo "sql lab : ".$sql_users2;
$query_users2 = ibase_query ($db_handle2, $sql_users2);
while ($row2 = ibase_fetch_row ($query_users2))
{
  if ( $row2[ $Tipo_Processo ] == "O" )  
  {
  $Resultados = "<b>PF:</b>".$row2[ $Uster_PNTFinos ]." <b>PG:</b>".$row2[ $Uster_PNTGrossos ]." <b>NP:</b>".$row2[ $Uster_Neps3 ]." <b>RK:</b>".$row2[ $Rkm_Valor ];
  }
  else
  {
  $Resultados = "<b>PF:</b>".$row2[ $Uster_PNTFinos ]." <b>PG:</b>".$row2[ $Uster_PNTGrossos ]." <b>NP:</b>".$row2[ $Uster_Neps2 ]." <b>RK:</b>".$row2[ $Rkm_Valor ];
  }
}



//echo "entrou !!!!";
//  $Factor = 0.985;
//if 
  $Preco  = $row[ $C_Preco ];
  $Preco2 = $row[ $C_Preco2 ];

 // Calcular Preco Medio de Custo Ponderado 
 $Qt = $row[ $C_QtExist ] - $row[ $C_QtReserv ];
 if ( $Qt > 0 )
 {
   $PMC_Qt = $PMC_Qt  + $Qt;
   $PMC_Exist = $PMC_Exist  + $Qt * $row[ $C_PCusto ];
   
   if ( $PMC_Qt > 0 ) 
   { 
     $PMC = $PMC_Exist / $PMC_Qt;
   } else { 
     $PMC = $row[ $C_PCusto ];
   }
   
   $PMC_Exist = $PMC_Qt * $PMC;
 }
 
 $Qt2 = $row[ $C_QtDisp ];
 if ( $Qt2 > 0 )
 {
   $PMC_Qt2 = $PMC_Qt2  + $Qt2;
   $PMC_Exist2 = $PMC_Exist2  + $Qt2 * $row[ $C_PCusto ];
   
   if ( $PMC_Qt2 > 0 ) 
   { 
     $PMC2 = $PMC_Exist2 / $PMC_Qt2;
   } else { 
     $PMC2 = $row[ $C_PCusto ];
   }
   
   $PMC_Exist2 = $PMC_Qt2 * $PMC2;
 }
 
//  If ( ( $Preco2 == $Preco ) And ( $Preco3 == $Preco ) ) $Preco2 = $Preco * $Factor;

//  if ( $row[ $C_TipoNivel ] == "T" )
//  {
//    $Preco  = $row[ $C_Preco3 ];
//    $Preco2 = $row[ $C_Preco3 ] * $Factor;
//  }
//  if ( $row[ $C_TipoNivel ] == "F" ) 
//  {
//    $Preco  = $row[ $C_Preco4 ];
//    $Preco2 = $row[ $C_Preco4 ] * $Factor;
//  }

  //$corfundo = "bgcolor=\"#FFFFFF\"";
  //if ( $row[ $C_TipoNivel ] == "T" ) $corfundo = "bgcolor=\"#00FF00\"";  // VERDE
  //if ( $row[ $C_TipoNivel ] == "P" ) $corfundo = "bgcolor=\"#00FF00\"";  // VERDE
  //if ( $row[ $C_TipoNivel ] == "N" ) $corfundo = "bgcolor=\"#FF9933\"";  // LARANJA
  //if ( $row[ $C_TipoNivel ] == "F" ) $corfundo = "bgcolor=\"#FF9933\"";  // LARANJA
  //if ( $row[ $C_TipoNivel ] == "X" ) $corfundo = "bgcolor=\"#FFFFFF\"";  // BRANCO

  $corfundo = "bgcolor=\"#".$row[ $C_Codigo_Cor ]."\"";
  
        echo "<tr ".$corfundo.">";

        echo "<td nowrap rowspan=0 align=\"right\"><font Size=\"2\" face=\"Tahoma\" width=75> <a style=\"text-decoration:none\" href=\"pedido.php?&Codigo=".$row[ $C_Codigo ]."&Armazem=".$row[ $C_Armazem ]."&Lote=".$row[ $C_Lote ]."&Quant=".$row[ $C_QtDisp ]."&Preco=".$Preco."\"> ".number_format($row[ $C_QtExist ], 2, chr(44), " ")." </a></td>";
        echo "<td nowrap rowspan=0 align=\"right\"><font Size=\"2\" face=\"Tahoma\" width=75> <a style=\"text-decoration:none\" href=\"listareserv.php?&Codigo=".$row[ $C_Codigo ]."&Lote=".$row[ $C_Lote ]."&Fornecedor=".$row[ $C_Fornecedor ]."\"> ".number_format($row[ $C_QtReserv ], 2, chr(44), " ")." </a></td>";
        echo "<td nowrap rowspan=0 align=\"right\"><font Size=\"2\" face=\"Tahoma\" width=75> <a style=\"text-decoration:none\" href=\"listaencforn.php?&Codigo=".$row[ $C_Codigo ]."&Lote=".$row[ $C_Lote ]."&Fornecedor=".$row[ $C_Fornecedor ]."\"> ".number_format($row[ $C_QtDisp ], 2, chr(44), " ")."</td>";

        echo "<td nowrap rowspan=0 align=\"center\"><font Size=\"2\" face=\"Tahoma\">  <a style=\"text-decoration:none\" href=\"listaresultados.php?&Codigo=".$row[ $C_Codigo ]."&Lote=".$row[ $C_Lote ]."\"> ".$Resultados."</td>";

        echo "<td height=\"20\" align=\"center\"><font Size=\"2\" face=\"Tahoma\">  <a style=\"text-decoration:none\" href=\"listaobslab.php?&Codigo=".$row[ $C_Codigo ]."&Lote=".$row[ $C_Lote ]."&DescSitua=".$row[ 20 ]."\"> ".$row[ $C_Restricao ]."</td>";

        if ( $nivel > 0 )
        {    
        echo "<td height=\"20\" nowrap rowspan=0 align=\"left\"><font Size=\"2\" face=\"Tahoma\" width=75> <a style=\"text-decoration:none\" href=\"listaextartlote.php?&Codigo=".$row[ $C_Codigo ]."&Lote=".$row[ $C_Lote ]."\"> ".$row[ $C_NomeForn ]."</td>";
        }
        echo "<td height=\"20\" nowrap rowspan=0 align=\"left\"><font Size=\"2\" face=\"Tahoma\" width=75>  <a style=\"text-decoration:none\" href=\"listaextartlote.php?&Codigo=".$row[ $C_Codigo ]."&Lote=".$row[ $C_Lote ]."\"> ".$row[ $C_Lote ]."</td>";
        
        //if ( $_SESSION["cd_vend"] == 1)
        //{
        //   echo "<td align=\"center\"><font Size=\"2\" face=\"Tahoma\">  <a style=\"text-decoration:none\" href=\"listaObsLab.php?&Codigo=".$row[ $C_Codigo ]."&Lote=".$row[ $C_Lote ]."\"> ".$row[ $C_Restricao ]."</td>";
        //}
        //else
        //{
        //  $flag = '';
        //  if ( substr( $row[ $C_Restricao ], strlen( $row[ $C_Restricao ] ) - 2, 2) == "BR" ) $flag = 'Branco';
        //  if ( ( substr( $row[ $C_Restricao ], strlen( $row[ $C_Restricao ] ) - 1, 1) == "S" ) And ( $row[ $C_Restricao ] <> "ANLS" ) )
        //  {
        //    $flag = 'Antracite';
        //  }
        //  if ( $row[ $C_Restricao ] == "FRAC" ) $flag = 'Fraco';
        //  echo "<td nowrap rowspan=0 align=\"center\"><font Size=\"2\" face=\"Tahoma\"> <a style=\"text-decoration:none\" href=\"listaLabObs.php?&Codigo=".$row[ $C_Codigo ]."&Lote=".$row[ $C_Lote ]."\"> ".$flag."</td>";
        //}
        // echo "<td nowrap rowspan=0 align=\"left\"><font Size=\"2\" face=\"Tahoma\">".$row[ $C_Descricao ]." </a></td>";

        echo "<td height=\"20\" nowrap rowspan=0 align=\"center\"><font Size=\"2\" face=\"Tahoma\"><b>".number_format( $Preco, 2, chr(44), " ")." </a></b></td>";
        echo "<td height=\"20\" nowrap rowspan=0 align=\"center\"><font Size=\"2\" face=\"Tahoma\">".number_format( $Preco2, 2, chr(44), " ")." </a></td>";

        if ( $nivel > 0 )
        {
          If ( $row[ $C_Fixacao ] == "S" ) 
          {
            echo "<td height=\"20\" nowrap rowspan=0 align=\"right\"><font color=\"#0000FF\" Size=\"2\" face=\"Tahoma\"><b>".number_format( $row[ $C_PCusto ], 2, chr(44), " ")." </a></td>";
          } else {
            echo "<td height=\"20\" nowrap rowspan=0 align=\"right\"><font color=\"#FF0000\" Size=\"2\" face=\"Tahoma\"><b>".number_format( $row[ $C_PCusto ], 2, chr(44), " ")." </a></td>";
          }    
        }

//        echo "<td nowrap rowspan=0 align=\"right\"><font Size=\"2\" face=\"Tahoma\" width=75>  <a style=\"text-decoration:none\" > ".number_format($row[ $C_Armazem ], 0, chr(44), " ")."</td>";

        if ( $nivel > 1 )
        {
          //$sCompra = $row[ $C_Moeda ]." ".number_format($row[ $C_PCompra ], 2, chr(44), " ")." - ".$row[ $C_CdEntrega ]." ".$row[ $Forma_Pag_Desc ]." ".number_format($row[ $Prazo_NDias ], 0, chr(44), " ");
          $sCompra = $row[ $C_Moeda ]." ".number_format($row[ $C_PCompra ], 2, chr(44), " ")." - ".$row[ $Forma_Pag_Desc ]." ".number_format($row[ $Prazo_NDias ], 0, chr(44), " ");

          echo "<td height=\"20\" nowrap rowspan=0 align=\"left\"><font Size=\"2\" face=\"Tahoma\">".$sCompra." </a></td>";

        }

        $salto = $salto."<BR>";

        echo "</tr>";

}

// Preco Medio de Custo Ponderado
if ( $nivel > 0 )
{
   if ( $PMC_Qt > 0 ) 
   { 
     $PMC = $PMC_Exist / $PMC_Qt;
   } else { 
     $PMC = 0;
   }
   if ( $PMC_Qt2 > 0 ) 
   { 
     $PMC2 = $PMC_Exist2 / $PMC_Qt2;
   } else { 
     $PMC2 = 0;
   }

  
// echo "<td style=\"font-size: 10pt\" align=\"right\" colspan=8 ><font color=\"#254117\" Size=\"2\" face=\"Tahoma\"><b>Precos Medios...</b></td>";
 echo "<td height=\"20\" style=\"font-size: 10pt\" align=\"right\" colspan=8 ><font Size=\"2\" face=\"Tahoma\"><b>Precos Medios...</b></td>";
 echo "<td height=\"20\" nowrap rowspan=0 align=\"right\"><font Size=\"2\" face=\"Tahoma\"><b>".number_format( $PMC, 2, chr(44), " ")." </a></td>";
 echo "<td height=\"20\" nowrap rowspan=0 align=\"right\"><font Size=\"2\" face=\"Tahoma\"><b>".number_format( $PMC2, 2, chr(44), " ")." </a></td>";
}

 echo "<td></td>";
 echo "</tr>";

echo "</table>";

ibase_close ($db_handle);

//$salto = $salto."<BR><BR><BR>";
//echo $salto;

?>



</body>

</FORM>
<FORM>

</FORM>

</html>



 e repara que quando clico na existencia ele chama o seguinte codigo ( pedido.php ):  <SCRIPT language="JavaScript">
function OnSubmitForm()
{
  if(document.pressed == 'Validar') document.myform.action ="validapedido.php";
  return true;
}
</SCRIPT> 

<?php
  session_start();

  include("private/vars.php");

  include("private/validar.php");
?>

<FORM NAME="myform" onSubmit="return OnSubmitForm();" METHOD=GET>
<meta name="viewport" content="width=240">
<?php
$C_Descricao = 0;
$C_Pvp1      = 1;
$C_Pvp2      = 2;

$P_Codigo   = $_GET["Codigo"];
$P_Armazem  = $_GET["Armazem"];
$P_Lote     = $_GET["Lote"];
$P_Cliente  = $_GET["Cliente"];
$P_Preco    = $_GET["Preco"];
$P_Quant    = $_GET["Quant"];
$P_Obs      = $_GET["Obs"];

$_SESSION["Codigo"]  = $P_Codigo;
$_SESSION["Armazem"] = $P_Armazem;
$_SESSION["Obs"]     = $P_Obs;

// Apanhar Preço segundo as regras defenidas

// Se Relacao Toma precedencia....
$_SESSION[ "RelP_Qt1"] = 0;
$_SESSION[ "RelP_Qt2"] = 0;
$db_handle = ibase_pconnect ($db_host, $db_username, $db_password);
$sql_users = "Select Preco1, Preco2 From RelArtLote_Preco Where Codigo = '".$P_Codigo."' And Lote = '".$P_Lote."'";
$query_users = ibase_query ($db_handle, $sql_users);
while ($row = ibase_fetch_row ($query_users ) )
{
  $_SESSION[ "RelP_Qt1"] = $row[ 0 ];
  $_SESSION[ "RelP_Qt2"] = $row[ 1 ];
  If ( empty( $P_Preco ) ) $P_Preco = $row[ 0 ];

}
ibase_close ($db_handle );

$_SESSION[ "P_Qt1"] = 0;
$_SESSION[ "P_Qt2"] = 0;
$db_handle = ibase_pconnect ($db_host, $db_username, $db_password);
$sql_users = "Select Descricao, P_Qt1, P_Qt2 From Artigos Where Codigo = '".$P_Codigo."'";
$query_users = ibase_query ($db_handle, $sql_users);
while ($row = ibase_fetch_row ($query_users ) )
{
  $P_Descricao = $row[0];
  If ( empty( $P_Preco ) ) $P_Preco = $row[ 1 ];

  $_SESSION[ "P_Qt1"] = $row[ 1 ];
  $_SESSION[ "P_Qt2"] = $row[ 2 ];

  $_SESSION[ "Descricao" ] = $P_Descricao;
}
  ibase_close ($db_handle );

// Se quantidade a zero sugerir existencia disponivel
if ( ( empty( $P_Quant ) ) Or ( $P_Quant <= 0 ) )
{
  $P_Quant = 0;
  $db_handle = ibase_pconnect ($db_host, $db_username, $db_password);
  $sql_users = "Select (RExist - REncCli + REncFor) as RStkDisp From Inq_Exist_Lote_Pda_2('".$P_Codigo."', '"
               .$P_Codigo."', ".$arm_ini.", ".$arm_fim.", 'ACT', 0, '31.12.3000', 'S', '31.12.3000', 0, 'S', 1, 2, 2)"
               ." Where RLote = '".$P_Lote."'";
  $query_users = ibase_query ($db_handle, $sql_users);
  while ($row = ibase_fetch_row ($query_users ) )
  {
    If ( ( $row[0] ) > 0 ) $P_Quant = $row[0];
    $_SESSION["Existencia"] = $P_Quant;
  }
//  if ( ( $P_Quant == 0 ) And ( empty( $P_Obs ) ) ) $P_Lote = "";
  ibase_close ($db_handle );
}

//echo "Codigo : ".$P_Codigo;
//echo "<BR>Lote : ".$P_Lote;
//echo "<BR><BR>Cliente : ".$P_Cliente;
//echo "<BR><BR>Preco : ".$P_Preco;
//echo "<BR><BR>Obs : ".$P_Obs;
//echo "<BR><BR>";

?>


<html>
  <head>
    <title>Obs Laboratorio</title>
  </head>
  <BODY bgcolor="#ffffff" text="black"><font face="arial,verdana,helvetica" size=3>


<select style="width: 215px;color: blue;font-size: 16px" name="Cliente" >
<?php
  // Set Database Access Info
  $db_handle = ibase_connect ($db_host, $db_username, $db_password );
  $sql_users = "Select l.cliente, l.Nome1, c.Situacao, rc2.vendedor "
              ."From Locais_Entrega l"
              ."  Left outer join clientes c on c.cliente = l.cliente"
              ."  Left Outer join Rel_Cli_Vend2 rc2 on rc2.cliente = l.cliente"
              ." where ( c.situacao in ( 'ACT', 'MANUT' ) ) And ( ( l.vendedor = ".$_SESSION["cd_vend"]." ) Or ( rc2.vendedor = ".$_SESSION["cd_vend"]." ) Or ( ".$_SESSION["cd_vend"]."= 1 )) Order By l.Nome1";
  $query_users = ibase_query ($db_handle, $sql_users);

  // Carregar Array Tipos de Processo
  while ($row = ibase_fetch_row ($query_users ) )
  {
     If ( empty( $P_Cliente ) )
     {
         echo "<option style=\"color: red\" value=\"$row[0]\"> ".$row[1]." </option>";
     } else
     {
       if ( $row[ 0 ] == $P_Cliente )
       {
         echo "<option style=\"color: red\" value=\"$row[0]\" Selected > ".$row[1]." </option>";
       } else {
         echo "<option style=\"color: red\" value=\"$row[0]\"> ".$row[1]." </option>";
       }
     }
  }
  ibase_close ($db_handle );
?>
</select>

<?php echo "<a style=\"font-weight:bold;font-size: 8pt;color: red\"\a><BR>"; ?>
<?php echo "<BR><a style=\"font-weight:bold;font-size: 10pt;color: red\"\a>".SubStr( $P_Descricao, 0, 60 )."<BR><BR>"; ?>

<table border='0' cellspacing='0' cellpadding='0' align=left>

<tr>
<?php echo "<td height=\"21\" nowrap ><INPUT style=\"font-weight:bold;color: blue;width: 85;text-align: center;font-size: 13px\" value='".number_format($P_Preco, 2, ',', '')."' TYPE=TEXT NAME=\"Preco\"></td>";?>
<?php echo "<td nowrap ><INPUT style=\"font-weight:bold;color: blue;width: 130;text-align: center;font-size: 13px\" value='".number_format($P_Quant, 2, ',', '.')."' TYPE=TEXT NAME=\"Quantidade\"></td>";?>
</tr>

<tr>
<?php echo "<td> Entrega </td>";?>
<?php echo "<td nowrap ><INPUT style=\"width: 130;text-align: center;font-size: 12px\" value='".date("d-m-Y")."' TYPE=TEXT NAME=\"Entrega\"></td>";?>
<!-- <td nowrap ><INPUT style="width: 130;text-align: left;font-size: 12px" TYPE=TEXT NAME="Entrega"></td> !-->
</tr>

<tr>
<?php echo "<td height=\"21\" nowrap ><INPUT style=\"width: 85;text-align: center;font-size: 12px\" value='".$P_Lote."' TYPE=TEXT NAME=\"Lote\"></td>";?>
<td nowrap ><INPUT style="width: 130;text-align: Center;font-size: 12px" Value="Morada do Cliente" TYPE=TEXT NAME="LocalEntrega"></td>
</tr>

<tr>
<?php echo "<td height=\"21\" nowrap ><INPUT style=\"width: 85;text-align: center;font-size: 12px\" TYPE=TEXT value=\"Alteracoes\" NAME=\"Local\"></td>";?>
<?php echo "<td nowrap ><INPUT style=\"width: 130;text-align: center;font-size: 12px\" value='".$P_Obs."' TYPE=TEXT NAME=\"Obs\"></td>";?>
</tr>

<tr>
<?php echo "<td height=\"21\" nowrap ><INPUT style=\"width: 85;text-align: center;font-size: 12px\" TYPE=TEXT value=\"Observacoes\" NAME=\"observacoes2\"></td>";?>
<td nowrap ><INPUT style="width: 130;text-align: center;font-size: 12px" TYPE=TEXT NAME="Obs2"></td>
</tr>

</table>

<BR><BR><BR><BR><BR><BR><BR><BR>

<INPUT style="width: 103px;text-align:center;height:30;font-size: 22px"   TYPE=SUBMIT VALUE="Validar" onClick="document.pressed=this.value" VALUE="Validar">

<INPUT style="width: 103px;text-align:center;height:30;font-size: 22px"   TYPE="button" VALUE="Menu" onclick="location.href='menu.php'">

</html>


 entao cria um form para o botao pedido com base no codigo do pedido.php
- faz sempre restart do servico apache2.service e outros que consideres necessarios apos alteracoes ao codigo
- na bd gescom_risatel os campos data passam a dt_registo e os campos local passam a local_id