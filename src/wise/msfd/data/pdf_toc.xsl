<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:outline="http://wkhtmltopdf.org/outline"
                xmlns="http://www.w3.org/1999/xhtml">
    <xsl:output doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN"
                doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd"
                indent="yes" />
    <xsl:function name="outline:getPrecedingItemsCount">
        <xsl:param name="currentNode"/>

        <xsl:value-of select="count($currentNode/preceding-sibling::*:item) + 1"/>
    </xsl:function>

    <xsl:function name="outline:getItemNumbering">
        <xsl:param name="currentNode"/>
        <xsl:param name="parentNumber"/>

        <xsl:choose>
            <xsl:when test="$currentNode/parent::*:item[@title != '']">
                <xsl:value-of
                    select="outline:getItemNumbering(
                        $currentNode/parent::*:item,
                        concat(string(outline:getPrecedingItemsCount($currentNode)), '. ', $parentNumber)
                    )"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="concat(string(outline:getPrecedingItemsCount($currentNode)), '. ', $parentNumber)"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:function>

    <xsl:template match="outline:outline">
        <html>
            <head>
                <title>Table of Contents</title>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                <style>
                    h1 {
                        text-align: left;
                        font-size: 1.2em;
                        font-family: arial;
                    }
                    div {
                        border-bottom: 1px dashed rgb(200,200,200);
                    }
                    span {
                        float: right;
                    }
                    li {
                        list-style: none;
                        margin-top: 5px;
                    }
                    ul {
                        font-size: 1em;
                        font-family: arial;
                        padding-left: 0em;
                    }
                    ul ul {
                        font-size: 90%;
                        padding-left: 1em;
                    }
                    a {
                        text-decoration: none;
                        color: black;
                    }
                    .table-of-contents {
                        font-size: 20px;
                        font-weight: bold;
                        border-bottom: 0px;
                    }
                </style>
            </head>
            <body>
                <div class="table-of-contents">Table of Contents</div>
                <ul><xsl:apply-templates select="outline:item/outline:item"/></ul>
            </body>
        </html>
    </xsl:template>
    <xsl:template match="outline:item">
        <li>
            <xsl:if test="@title != ''">
                <div class="content-item">
                    <a>
                        <xsl:if test="@link">
                            <xsl:attribute name="href"><xsl:value-of select="@link"/></xsl:attribute>
                        </xsl:if>
                        <xsl:if test="@backLink">
                            <xsl:attribute name="name"><xsl:value-of select="@backLink"/></xsl:attribute>
                        </xsl:if>
                        <xsl:value-of select="outline:getItemNumbering(., '')"/>
                        <xsl:value-of select="@title" />
                    </a>
                    <span> <xsl:value-of select="@page + 1" /> </span>
                </div>
            </xsl:if>
            <ul>
                <xsl:comment>added to prevent self-closing tags in QtXmlPatterns</xsl:comment>
                <xsl:apply-templates select="outline:item"/>
            </ul>
        </li>
    </xsl:template>
</xsl:stylesheet>