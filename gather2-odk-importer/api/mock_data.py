# coding=utf-8

XFORM_XML = """
<?xml version="1.0" encoding="UTF-8"?>
<!--$Id: eg-00.xml,v 1.2 2003/10/23 15:27:04 tvraman Exp $-->
<html xmlns="http://www.w3.org/2002/06/xhtml2"
      xmlns:xforms="http://www.w3.org/2002/xforms"
      xmlns:xsd="http://www.w3.org/2001/XMLSchema"
      xmlns:ev="http://www.w3.org/2001/xml-events"
      xmlns:my="http://commerce.example.com/payment">
  <head>
    <title xml:lang="fr">XForms en XHTML</title>
    <xforms:model schema="payschema.xsd">
      <xforms:instance>
        <my:payment as="credit">
          <my:cc/>
          <my:exp/>
        </my:payment>
      </xforms:instance>
      <xforms:submission action="http://www.example.com/buy.rb" method="post" id="s00"/>
      <xforms:bind nodeset="my:cc" relevant="../@as='credit'" required="true()"/>
      <xforms:bind nodeset="my:exp" relevant="../@as='credit'" required="true()"/>
    </xforms:model>
  </head>
  <body>
    ...
    <group xmlns="http://www.w3.org/2002/xforms">
      <trigger>
        <label>Français</label>
        <toggle case="fr" ev:event="xforms-activate"/>
      </trigger>
      <trigger>
        <label>English</label>
        <toggle case="en" ev:event="xforms-activate"/>
      </trigger>
    </group>
    <switch xmlns="http://www.w3.org/2002/xforms">
      <case id="fr">
        <select1 ref="@as">
          <label xml:lang="fr">Choisissez un mode de paiement</label>
          <choices>
            <item>
              <label xml:lang="fr">Comptant</label>
              <value>cash</value>
              <message level="modeless" ev:event="xforms-select" xml:lang="fr">
                         Ne pas envoyer d'argent comptant par la poste.</message>
            </item>
            <item>
              <label xml:lang="fr">Carte bancaire</label>
              <value>credit</value>
            </item>
          </choices>
        </select1>
        <input ref="my:cc">
          <label xml:lang="fr">Numéro de carte bancaire</label>
          <alert xml:lang="fr">Saississez un numéro de carte bancaire en cours
           (séparez par un espace ou un trait d'union chaque groupe de chiffres)</alert>
        </input>
        <input ref="my:exp">
          <label xml:lang="fr">Date d'échéance</label>
        </input>
        <submit submission="s00">
          <label xml:lang="fr">Achetez</label>
        </submit>
      </case>
      <case id="en">
        <select1 ref="@as">
          <label xml:lang="en">Select Payment Method</label>
          <choices>
            <item>
              <label xml:lang="en">Cash</label>
              <value>cash</value>
              <message level="modeless" ev:event="xforms-select" xml:lang="en">
              Please do not mail cash.</message>
            </item>
            <item>
              <label xml:lang="en">Credit</label>
              <value>credit</value>
            </item>
          </choices>
        </select1>
        <input ref="my:cc">
          <label xml:lang="en">Credit Card Number</label>
          <alert xml:lang="en">Please specify a valid credit card number
            (use spaces or hyphens between digit groups)</alert>
        </input>
        <input ref="my:exp">
          <label xml:lang="en">Expiration Date</label>
        </input>
        <submit submission="s00">
          <label xml:lang="en">Buy</label>
        </submit>
      </case>
    </switch>
    ...
  </body>
</html>
"""
