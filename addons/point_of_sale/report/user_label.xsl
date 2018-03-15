<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    version="1.0" 
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:fo="http://www.w3.org/1999/XSL/Format">
    <xsl:variable name="initial_bottom_pos">24.5</xsl:variable>
    <xsl:variable name="initial_left_pos">0.5</xsl:variable>
    <xsl:variable name="height_increment">4.8</xsl:variable>
    <xsl:variable name="width_increment">10</xsl:variable>
    <xsl:variable name="frame_height">3cm</xsl:variable>
    <xsl:variable name="frame_width">9.3cm</xsl:variable>
    <xsl:variable name="number_columns">2</xsl:variable>
    <xsl:variable name="max_frames">16</xsl:variable>

    <xsl:template match="/">
        <xsl:apply-templates select="lots"/>
    </xsl:template>

    <xsl:template match="lots">
        <document>
            <template leftMargin="2.0cm" rightMargin="2.0cm" topMargin="2.0cm" bottomMargin="2.0cm" title="Address list" author="Generated by Open ERP">
                <pageTemplate id="all">
                    <pageGraphics/>
                    <xsl:apply-templates select="lot-line" mode="frames"/>
                </pageTemplate>
            </template>
            <stylesheet>
                <paraStyle name="nospace" fontName="Courier" fontSize="10" spaceBefore="0" spaceAfter="0"/>
                <blockTableStyle id="mytable">
                    <blockBackground colorName="lightred" start="0,0" stop="0,0"/>
                    <blockBackground colorName="lightgrey" start="1,0" stop="-1,0"/>
                    <blockAlignment value="CENTER"/>
                    <blockValign value="MIDDLE"/>
                    <blockFont name="Helvetica-BoldOblique" size="14" start="0,0" stop="-1,0"/>
                    <blockFont name="Helvetica" size="8" start="0,1" stop="-1,1"/>
                    <lineStyle kind="GRID" colorName="black" tickness="1"/>
                </blockTableStyle>
            </stylesheet>
            <story>
                <xsl:apply-templates select="lot-line" mode="story"/>
            </story>
        </document>
    </xsl:template>

    <xsl:template match="lot-line" mode="frames">
        <xsl:if test="position() &lt; $max_frames + 1">
            <frame>
                <xsl:attribute name="width">
                    <xsl:value-of select="$frame_width"/>
                </xsl:attribute>
                <xsl:attribute name="height">
                    <xsl:value-of select="$frame_height"/>
                </xsl:attribute>
                <xsl:attribute name="x1">
                    <xsl:value-of select="$initial_left_pos + ((position()-1) mod $number_columns) * $width_increment"/>
                    <xsl:text>cm</xsl:text>
                </xsl:attribute>
                <xsl:attribute name="y1">
                    <xsl:value-of select="$initial_bottom_pos - floor((position()-1) div $number_columns) * $height_increment"/>
                    <xsl:text>cm</xsl:text>
                </xsl:attribute>
            </frame>
        </xsl:if>
    </xsl:template>

    <xsl:template match="lot-line" mode="story">
        <blockTable style="mytable" colWidths="2.8cm,5.4cm">
            <tr>
                <td>
                    <para style="nospace"></para>
                </td>
                <td>
                    <para style="nospace" t="1">
                        <!--
                        <xsl:value-of select="price"/> <xsl:value-of select="currency"/>
                        -->
                    </para>
                </td>
            </tr>
            <tr>
                <td>
                    <barCode><xsl:value-of select="ean13" /></barCode> 
                </td>
                <td>
                    <para style="nospace"><xsl:value-of select="username"/></para>
                </td>
            </tr>
        </blockTable>
        <nextFrame/>
    </xsl:template>
</xsl:stylesheet>
