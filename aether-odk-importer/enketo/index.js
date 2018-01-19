var $ = require( 'jquery' );
var Form = require('enketo-core');

// var model = `
// <model><instance>
//         <widgets xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms" id="widgets" version="201708012229">
//           <formhub>
//             <uuid/>
//           </formhub>
//           <intro/>
//           <text_widgets>
//             <text/>
//             <long_text/>
//           </text_widgets>
//           <number_widgets>
//             <int/>
//             <decimal>18.31</decimal>
//             <s/>
//           </number_widgets>
//           <date_time_widgets>
//             <date>2010-06-15</date>
//             <date_month_year/>
//             <date_year/>
//             <time/>
//             <datetime/>
//           </date_time_widgets>
//           <select_widgets>
//             <select>a c</select>
//             <select_horizontal_compact/>
//             <select_horizontal/>
//             <select_spinner/>
//             <select1>8</select1>
//             <select1_horizontal_compact/>
//             <select1_horizontal/>
//             <select1_likert/>
//             <select1_spinner/>
//             <select1_autocomplete/>
//             <grid_test/>
//             <grid_2_columns/>
//             <table_list_test>
//               <table_list_test_label/>
//               <table_list_1/>
//               <table_list_2/>
//             </table_list_test>
//             <table_list_test2>
//               <generated_table_list_label_37/>
//               <reserved_name_for_field_list_labels_38/>
//               <table_list_3/>
//               <table_list_4/>
//             </table_list_test2>
//             <happy_sad_table_2>
//               <happy_sad_second_method/>
//               <happy_sad_brian2/>
//               <happy_sad_michael2/>
//             </happy_sad_table_2>
//             <happy_sad_table>
//               <generated_table_list_label_46/>
//               <reserved_name_for_field_list_labels_47/>
//               <happy_sad_brian/>
//               <happy_sad_michael/>
//             </happy_sad_table>
//           </select_widgets>
//           <cascading_widgets>
//             <group1>
//               <country/>
//               <city/>
//               <neighborhood/>
//             </group1>
//             <group2>
//               <country2/>
//               <city2/>
//               <neighborhood2/>
//             </group2>
//           </cascading_widgets>
//           <geopoint_widgets>
//             <geopoint/>
//             <geopoint_m/>
//             <geopoint_hide/>
//             <geotrace/>
//             <geoshape>7.9377 -11.5845 0 0;7.9324 -11.5902 0 0;7.927 -11.5857 0 0;7.925 -11.578 0 0;7.9267 -11.5722 0 0;7.9325 -11.5708 0 0;7.9372 -11.5737 0 0;7.9393 -11.579 0 0;7.9377 -11.5845 0 0</geoshape>
//           </geopoint_widgets>
//           <media_widgets>
//             <image/>
//             <draw/>
//             <signature/>
//             <annotate/>
//             <my_audio/>
//             <my_video/>
//             <my_barcode/>
//           </media_widgets>
//           <display_widgets>
//             <my_output/>
//             <text_media/>
//             <select_media/>
//             <my_trigger/>
//           </display_widgets>
//           <meta>
//             <instanceID/>
//           </meta>
//         </widgets>
//       </instance><instance id="cities">
//         <root xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms">
//           <item>
//             <itextId>static_instance-cities-0</itextId>
//             <country>nl</country>
//             <name>ams</name>
//           </item>
//           <item>
//             <itextId>static_instance-cities-1</itextId>
//             <country>usa</country>
//             <name>den</name>
//           </item>
//           <item>
//             <itextId>static_instance-cities-2</itextId>
//             <country>usa</country>
//             <name>nyc</name>
//           </item>
//           <item>
//             <itextId>static_instance-cities-3</itextId>
//             <country>usa</country>
//             <name>la</name>
//           </item>
//           <item>
//             <itextId>static_instance-cities-4</itextId>
//             <country>nl</country>
//             <name>rot</name>
//           </item>
//           <item>
//             <itextId>static_instance-cities-5</itextId>
//             <country>nl</country>
//             <name>dro</name>
//           </item>
//         </root>
//       </instance><instance id="neighborhoods">
//         <root xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms">
//           <item>
//             <itextId>static_instance-neighborhoods-0</itextId>
//             <country>usa</country>
//             <name>bronx</name>
//             <city>nyc</city>
//           </item>
//           <item>
//             <itextId>static_instance-neighborhoods-1</itextId>
//             <country>usa</country>
//             <name>harlem</name>
//             <city>nyc</city>
//           </item>
//           <item>
//             <itextId>static_instance-neighborhoods-2</itextId>
//             <country>usa</country>
//             <name>belair</name>
//             <city>la</city>
//           </item>
//           <item>
//             <itextId>static_instance-neighborhoods-3</itextId>
//             <country>nl</country>
//             <name>wes</name>
//             <city>ams</city>
//           </item>
//           <item>
//             <itextId>static_instance-neighborhoods-4</itextId>
//             <country>usa</country>
//             <name>parkhill</name>
//             <city>den</city>
//           </item>
//           <item>
//             <itextId>static_instance-neighborhoods-5</itextId>
//             <country>nl</country>
//             <name>haven</name>
//             <city>rot</city>
//           </item>
//           <item>
//             <itextId>static_instance-neighborhoods-6</itextId>
//             <country>nl</country>
//             <name>dam</name>
//             <city>ams</city>
//           </item>
//           <item>
//             <itextId>static_instance-neighborhoods-7</itextId>
//             <country>nl</country>
//             <name>centrum</name>
//             <city>rot</city>
//           </item>
//           <item>
//             <itextId>static_instance-neighborhoods-8</itextId>
//             <country>nl</country>
//             <name>haven</name>
//             <city>dro</city>
//           </item>
//         </root>
//       </instance><instance id="countries">
//         <root xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms">
//           <item>
//             <itextId>static_instance-countries-0</itextId>
//             <name>nl</name>
//           </item>
//           <item>
//             <itextId>static_instance-countries-1</itextId>
//             <name>usa</name>
//           </item>
//         </root>
//       </instance><instance id="list">
//         <root xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms">
//           <item>
//             <itextId>static_instance-list-0</itextId>
//             <name>a</name>
//           </item>
//           <item>
//             <itextId>static_instance-list-1</itextId>
//             <name>b</name>
//           </item>
//           <item>
//             <itextId>static_instance-list-2</itextId>
//             <name>c</name>
//           </item>
//           <item>
//             <itextId>static_instance-list-3</itextId>
//             <name>d</name>
//           </item>
//         </root>
//       </instance><instance id="a_b_c_d">
//         <root xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms">
//           <item>
//             <itextId>static_instance-a_b_c_d-0</itextId>
//             <name>a</name>
//           </item>
//           <item>
//             <itextId>static_instance-a_b_c_d-1</itextId>
//             <name>b</name>
//           </item>
//           <item>
//             <itextId>static_instance-a_b_c_d-2</itextId>
//             <name>c</name>
//           </item>
//           <item>
//             <itextId>static_instance-a_b_c_d-3</itextId>
//             <name>d</name>
//           </item>
//         </root>
//       </instance><instance id="list1">
//         <root xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms">
//           <item>
//             <itextId>static_instance-list1-0</itextId>
//             <name>king</name>
//           </item>
//           <item>
//             <itextId>static_instance-list1-1</itextId>
//             <name>pig</name>
//           </item>
//           <item>
//             <itextId>static_instance-list1-2</itextId>
//             <name>nut</name>
//           </item>
//         </root>
//       </instance><instance id="happy_sad">
//         <root xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms">
//           <item>
//             <itextId>static_instance-happy_sad-0</itextId>
//             <name>happy</name>
//           </item>
//           <item>
//             <itextId>static_instance-happy_sad-1</itextId>
//             <name>sad</name>
//           </item>
//         </root>
//       </instance><instance id="list2">
//         <root xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms">
//           <item>
//             <itextId>static_instance-list2-0</itextId>
//             <name>1</name>
//           </item>
//           <item>
//             <itextId>static_instance-list2-1</itextId>
//             <name>2</name>
//           </item>
//           <item>
//             <itextId>static_instance-list2-2</itextId>
//             <name>3</name>
//           </item>
//           <item>
//             <itextId>static_instance-list2-3</itextId>
//             <name>4</name>
//           </item>
//           <item>
//             <itextId>static_instance-list2-4</itextId>
//             <name>5</name>
//           </item>
//           <item>
//             <itextId>static_instance-list2-5</itextId>
//             <name>6</name>
//           </item>
//           <item>
//             <itextId>static_instance-list2-6</itextId>
//             <name>7</name>
//           </item>
//           <item>
//             <itextId>static_instance-list2-7</itextId>
//             <name>8</name>
//           </item>
//         </root>
//       </instance><instance id="state">
//         <root xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms">
//           <item>
//             <itextId>static_instance-state-0</itextId>
//             <name>AK</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-1</itextId>
//             <name>HI</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-2</itextId>
//             <name>AL</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-3</itextId>
//             <name>AR</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-4</itextId>
//             <name>AZ</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-5</itextId>
//             <name>CA</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-6</itextId>
//             <name>CO</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-7</itextId>
//             <name>CT</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-8</itextId>
//             <name>DE</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-9</itextId>
//             <name>FL</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-10</itextId>
//             <name>GA</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-11</itextId>
//             <name>IA</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-12</itextId>
//             <name>ID</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-13</itextId>
//             <name>IL</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-14</itextId>
//             <name>IN</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-15</itextId>
//             <name>KS</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-16</itextId>
//             <name>LA</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-17</itextId>
//             <name>MA</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-18</itextId>
//             <name>MD</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-19</itextId>
//             <name>ME</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-20</itextId>
//             <name>MI</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-21</itextId>
//             <name>MN</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-22</itextId>
//             <name>MO</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-23</itextId>
//             <name>MS</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-24</itextId>
//             <name>MT</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-25</itextId>
//             <name>NC</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-26</itextId>
//             <name>ND</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-27</itextId>
//             <name>NE</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-28</itextId>
//             <name>NH</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-29</itextId>
//             <name>NJ</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-30</itextId>
//             <name>NM</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-31</itextId>
//             <name>NV</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-32</itextId>
//             <name>NY</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-33</itextId>
//             <name>OH</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-34</itextId>
//             <name>OK</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-35</itextId>
//             <name>OR</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-36</itextId>
//             <name>PA</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-37</itextId>
//             <name>SC</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-38</itextId>
//             <name>SD</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-39</itextId>
//             <name>TN</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-40</itextId>
//             <name>TX</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-41</itextId>
//             <name>UT</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-42</itextId>
//             <name>VA</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-43</itextId>
//             <name>VT</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-44</itextId>
//             <name>WA</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-45</itextId>
//             <name>WI</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-46</itextId>
//             <name>WV</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-47</itextId>
//             <name>WY</name>
//           </item>
//           <item>
//             <itextId>static_instance-state-48</itextId>
//             <name>DC</name>
//           </item>
//         </root>
//       </instance><instance id="a_b">
//         <root xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms">
//           <item>
//             <itextId>static_instance-a_b-0</itextId>
//             <name>a</name>
//           </item>
//           <item>
//             <itextId>static_instance-a_b-1</itextId>
//             <name>b</name>
//           </item>
//         </root>
//       </instance><instance id="agree5">
//         <root xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms">
//           <item>
//             <itextId>static_instance-agree5-0</itextId>
//             <name>1</name>
//           </item>
//           <item>
//             <itextId>static_instance-agree5-1</itextId>
//             <name>2</name>
//           </item>
//           <item>
//             <itextId>static_instance-agree5-2</itextId>
//             <name>3</name>
//           </item>
//           <item>
//             <itextId>static_instance-agree5-3</itextId>
//             <name>4</name>
//           </item>
//           <item>
//             <itextId>static_instance-agree5-4</itextId>
//             <name>5</name>
//           </item>
//         </root>
//       </instance><instance id="yes_no">
//         <root xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms">
//           <item>
//             <itextId>static_instance-yes_no-0</itextId>
//             <name>yes</name>
//           </item>
//           <item>
//             <itextId>static_instance-yes_no-1</itextId>
//             <name>no</name>
//           </item>
//           <item>
//             <itextId>static_instance-yes_no-2</itextId>
//             <name>dk</name>
//           </item>
//           <item>
//             <itextId>static_instance-yes_no-3</itextId>
//             <name>na</name>
//           </item>
//         </root>
//       </instance></model>`;

// HTML// varform= `
// HTML <form autocomplete="off" novalidate="novalidate" class="or clearfix theme-formhub" dir="ltr" id="widgets">
// <!--This form was created by transforming a OpenRosa-flavored (X)Form using an XSL stylesheet created by Enketo LLC.--><section class="form-logo"> </section><h3 dir="auto" id="form-title">Widgets</h3><select id="form-languages" style="display:none;" data-default-lang="default"><option value="default" data-dir="ltr">default</option> </select>


//     <label class="question note non-select "><span lang="" class="question-label active"><p>This form showcases the different available <em>widgets</em>.</p>
// <p>The hints explain how these widgets were created. The form logo was added by simply uploading a file called <em>form_logo.png</em> as part of the form media.</p>
// The XLS Form source is <a href="https://docs.google.com/spreadsheet/ccc?key=0Al3Mw5sknZoPdEpPa29tamFCc1o2bmFVR3RaemlSRXc&usp=sharing" target="_blank">here</a>.</span><input type="text" name="/widgets/intro" data-type-xml="string" readonly="readonly"/></label>
//     <section class="or-group " name="/widgets/text_widgets"><h4><span lang="" class="question-label active">Text widgets</span></h4><label class="question non-select "><span lang="" class="question-label active">Text widget</span><span lang="" class="or-hint active">Can be short or long but always one line (type = text)</span><input type="text" name="/widgets/text_widgets/text" data-type-xml="string"/></label><label class="question non-select or-appearance-multiline "><span lang="" class="question-label active">Multiline Text widget in enketo (in ODK collect this a normal text field)</span><span lang="" class="or-hint active">Can be multiple lines (type=text, appearance = multiline)</span><textarea name="/widgets/text_widgets/long_text" data-type-xml="string"> </textarea></label>
//             </section><!--end of group -->
//     <section class="or-group " name="/widgets/number_widgets"><h4><span lang="" class="question-label active">Number widgets</span></h4><label class="question non-select "><span lang="" class="question-label active">Integer widget (try entering a number &gt; 10)</span><span lang="" class="or-hint active">This field has a constraint (type=integer, constraint=.&lt;10)</span><input type="number" name="/widgets/number_widgets/int" data-constraint=". &lt; 10" data-type-xml="int"/><span lang="" class="or-constraint-msg active">number must be less than 10</span></label><label class="question non-select "><span lang="" class="question-label active">Decimal widget (allows only number &gt; 10.51 and &lt; 18.39)</span><span lang="" class="or-hint active">This field has a constraint (type=decimal, constraint=. &gt; 10.51 and . &lt; 18.39)</span><input type="number" name="/widgets/number_widgets/decimal" data-constraint=". &gt; 10.51 and . &lt; 18.39" data-type-xml="decimal" step="any"/><span lang="" class="or-constraint-msg active">number must be between 10.51 and 18.39</span></label><label class="question non-select or-appearance-distress "><span lang="" class="question-label active">Distress widget</span><span lang="" class="or-hint active">A highly specific widget to measure distress</span><input type="number" name="/widgets/number_widgets/s" data-constraint=". &gt;= 0 and . &lt;= 10" data-type-xml="int"/><span class="or-constraint-msg active" lang="" data-i18n="constraint.invalid">Value not allowed</span></label>
//             </section><!--end of group -->
//     <section class="or-group " name="/widgets/date_time_widgets"><h4><span lang="" class="question-label active">Date and time widgets</span></h4><label class="question non-select "><span lang="" class="question-label active">Date widget (this one allows only future dates and has a default value)</span><span lang="" class="or-hint active">This field has a constraint (type=date, constraint=.&gt;= today())</span><input type="date" name="/widgets/date_time_widgets/date" data-constraint=". &gt;= today()" data-type-xml="date"/><span lang="" class="or-constraint-msg active">only future dates allowed</span></label><label class="question non-select or-appearance-month-year "><span lang="" class="question-label active">Month-year widget</span><span lang="" class="or-hint active">Simply specify an appearance style (type=date, appearance=month-year)</span><input type="date" name="/widgets/date_time_widgets/date_month_year" data-type-xml="date"/></label><label class="question non-select or-appearance-year "><span lang="" class="question-label active">Year widget (year only)</span><span lang="" class="or-hint active">Simply specify and appearance style (type=date, appearance=year)</span><input type="date" name="/widgets/date_time_widgets/date_year" data-type-xml="date"/></label><label class="question non-select "><span lang="" class="question-label active">Time widget</span><span lang="" class="or-hint active">Times are easy! (type=time)</span><input type="time" name="/widgets/date_time_widgets/time" data-type-xml="time"/></label><label class="question non-select "><span lang="" class="question-label active">Date and time widget</span><span lang="" class="or-hint active">For exact times, will be converted to UTC/GMT (type=dateTime)</span><input type="datetime" name="/widgets/date_time_widgets/datetime" data-type-xml="dateTime"/></label>
//             </section><!--end of group -->
//     <section class="or-group " name="/widgets/select_widgets"><h4><span lang="" class="question-label active">Select widgets</span></h4><fieldset class="question simple-select "><fieldset><legend><span lang="" class="question-label active">Select multiple widget (don't pick c and d together)</span><span lang="" class="or-hint active">Using a list specified in the choices worksheet (type=select_multiple list)</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="checkbox" name="/widgets/select_widgets/select" value="a" data-constraint="not(selected(., 'c') and selected(., 'd'))" data-type-xml="select"/><span lang="" class="option-label active">option a</span></label><label class=""><input type="checkbox" name="/widgets/select_widgets/select" value="b" data-constraint="not(selected(., 'c') and selected(., 'd'))" data-type-xml="select"/><span lang="" class="option-label active">option b</span></label><label class=""><input type="checkbox" name="/widgets/select_widgets/select" value="c" data-constraint="not(selected(., 'c') and selected(., 'd'))" data-type-xml="select"/><span lang="" class="option-label active">option c</span></label><label class=""><input type="checkbox" name="/widgets/select_widgets/select" value="d" data-constraint="not(selected(., 'c') and selected(., 'd'))" data-type-xml="select"/><span lang="" class="option-label active">option d</span></label></div></fieldset><span lang="" class="or-constraint-msg active">option c and d cannot be selected together</span></fieldset><fieldset class="question simple-select or-appearance-horizontal-compact "><fieldset><legend><span lang="" class="question-label active">Select multiple widget displaying horizontally</span><span lang="" class="or-hint active">(type = select_multiple, appearance=horizontal-compact)</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="checkbox" name="/widgets/select_widgets/select_horizontal_compact" value="a" data-type-xml="select"/><span lang="" class="option-label active">option a</span></label><label class=""><input type="checkbox" name="/widgets/select_widgets/select_horizontal_compact" value="b" data-type-xml="select"/><span lang="" class="option-label active">option b</span></label><label class=""><input type="checkbox" name="/widgets/select_widgets/select_horizontal_compact" value="c" data-type-xml="select"/><span lang="" class="option-label active">option c</span></label><label class=""><input type="checkbox" name="/widgets/select_widgets/select_horizontal_compact" value="d" data-type-xml="select"/><span lang="" class="option-label active">option d</span></label></div></fieldset></fieldset><fieldset class="question simple-select or-appearance-horizontal "><fieldset><legend><span lang="" class="question-label active">Select multiple widget displaying horizontally in columns</span><span lang="" class="or-hint active">(type=select_multiple, appearance=horizontal)</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="checkbox" name="/widgets/select_widgets/select_horizontal" value="1" data-type-xml="select"/><span lang="" class="option-label active">option 1</span></label><label class=""><input type="checkbox" name="/widgets/select_widgets/select_horizontal" value="2" data-type-xml="select"/><span lang="" class="option-label active">option 2</span></label><label class=""><input type="checkbox" name="/widgets/select_widgets/select_horizontal" value="3" data-type-xml="select"/><span lang="" class="option-label active">option 3</span></label><label class=""><input type="checkbox" name="/widgets/select_widgets/select_horizontal" value="4" data-type-xml="select"/><span lang="" class="option-label active">option 4</span></label><label class=""><input type="checkbox" name="/widgets/select_widgets/select_horizontal" value="5" data-type-xml="select"/><span lang="" class="option-label active">option 5</span></label><label class=""><input type="checkbox" name="/widgets/select_widgets/select_horizontal" value="6" data-type-xml="select"/><span lang="" class="option-label active">option 6</span></label><label class=""><input type="checkbox" name="/widgets/select_widgets/select_horizontal" value="7" data-type-xml="select"/><span lang="" class="option-label active">option 7</span></label><label class=""><input type="checkbox" name="/widgets/select_widgets/select_horizontal" value="8" data-type-xml="select"/><span lang="" class="option-label active">option 8</span></label></div></fieldset></fieldset><label class="question or-appearance-minimal "><span lang="" class="question-label active">Select multiple: pulldown</span><span lang="" class="or-hint active">Showing a pull-down list of options (type=select_multiple list, appearance=minimal)</span><select multiple="multiple" name="/widgets/select_widgets/select_spinner" data-type-xml="select"><option value="">...</option><option value="a">option a</option><option value="b">option b</option><option value="c">option c</option><option value="d">option d</option></select><span class="or-option-translations" style="display:none;">
//                 </span></label><fieldset class="question simple-select "><fieldset><legend><span lang="" class="question-label active">Select one widget</span><span lang="" class="or-hint active">Scroll down to see default selection (type=select_one list2, default=8)</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="radio" name="/widgets/select_widgets/select1" data-name="/widgets/select_widgets/select1" value="1" data-type-xml="select1"/><span lang="" class="option-label active">option 1</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1" data-name="/widgets/select_widgets/select1" value="2" data-type-xml="select1"/><span lang="" class="option-label active">option 2</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1" data-name="/widgets/select_widgets/select1" value="3" data-type-xml="select1"/><span lang="" class="option-label active">option 3</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1" data-name="/widgets/select_widgets/select1" value="4" data-type-xml="select1"/><span lang="" class="option-label active">option 4</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1" data-name="/widgets/select_widgets/select1" value="5" data-type-xml="select1"/><span lang="" class="option-label active">option 5</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1" data-name="/widgets/select_widgets/select1" value="6" data-type-xml="select1"/><span lang="" class="option-label active">option 6</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1" data-name="/widgets/select_widgets/select1" value="7" data-type-xml="select1"/><span lang="" class="option-label active">option 7</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1" data-name="/widgets/select_widgets/select1" value="8" data-type-xml="select1"/><span lang="" class="option-label active">option 8</span></label></div></fieldset></fieldset><fieldset class="question simple-select or-appearance-horizontal-compact "><fieldset><legend><span lang="" class="question-label active">Select one widget displaying horizontally</span><span lang="" class="or-hint active">(type=select_one, appearance=horizontal-compact)</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="radio" name="/widgets/select_widgets/select1_horizontal_compact" data-name="/widgets/select_widgets/select1_horizontal_compact" value="yes" data-type-xml="select1"/><span lang="" class="option-label active">Yes</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1_horizontal_compact" data-name="/widgets/select_widgets/select1_horizontal_compact" value="no" data-type-xml="select1"/><span lang="" class="option-label active">No</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1_horizontal_compact" data-name="/widgets/select_widgets/select1_horizontal_compact" value="dk" data-type-xml="select1"/><span lang="" class="option-label active">Don't Know</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1_horizontal_compact" data-name="/widgets/select_widgets/select1_horizontal_compact" value="na" data-type-xml="select1"/><span lang="" class="option-label active">Not Applicable</span></label></div></fieldset></fieldset><fieldset class="question simple-select or-appearance-horizontal "><fieldset><legend><span lang="" class="question-label active">Select one widget displaying horizontally in colmns</span><span lang="" class="or-hint active">(type=select_one, appearance=horizontal)</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="radio" name="/widgets/select_widgets/select1_horizontal" data-name="/widgets/select_widgets/select1_horizontal" value="1" data-type-xml="select1"/><span lang="" class="option-label active">option 1</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1_horizontal" data-name="/widgets/select_widgets/select1_horizontal" value="2" data-type-xml="select1"/><span lang="" class="option-label active">option 2</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1_horizontal" data-name="/widgets/select_widgets/select1_horizontal" value="3" data-type-xml="select1"/><span lang="" class="option-label active">option 3</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1_horizontal" data-name="/widgets/select_widgets/select1_horizontal" value="4" data-type-xml="select1"/><span lang="" class="option-label active">option 4</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1_horizontal" data-name="/widgets/select_widgets/select1_horizontal" value="5" data-type-xml="select1"/><span lang="" class="option-label active">option 5</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1_horizontal" data-name="/widgets/select_widgets/select1_horizontal" value="6" data-type-xml="select1"/><span lang="" class="option-label active">option 6</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1_horizontal" data-name="/widgets/select_widgets/select1_horizontal" value="7" data-type-xml="select1"/><span lang="" class="option-label active">option 7</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1_horizontal" data-name="/widgets/select_widgets/select1_horizontal" value="8" data-type-xml="select1"/><span lang="" class="option-label active">option 8</span></label></div></fieldset></fieldset><fieldset class="question or-appearance-likert "><fieldset><legend><span lang="" class="question-label active">Select one displaying as a Likert item</span><span lang="" class="or-hint active">(type=select_one, appearance=likert)</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="radio" name="/widgets/select_widgets/select1_likert" data-name="/widgets/select_widgets/select1_likert" value="1" data-type-xml="select1"/><span lang="" class="option-label active">strongly disagree</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1_likert" data-name="/widgets/select_widgets/select1_likert" value="2" data-type-xml="select1"/><span lang="" class="option-label active">disagree</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1_likert" data-name="/widgets/select_widgets/select1_likert" value="3" data-type-xml="select1"/><span lang="" class="option-label active">neither agree nor disagree</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1_likert" data-name="/widgets/select_widgets/select1_likert" value="4" data-type-xml="select1"/><span lang="" class="option-label active">agree</span></label><label class=""><input type="radio" name="/widgets/select_widgets/select1_likert" data-name="/widgets/select_widgets/select1_likert" value="5" data-type-xml="select1"/><span lang="" class="option-label active">strongly agree</span></label></div></fieldset></fieldset><label class="question or-appearance-minimal "><span lang="" class="question-label active">Select one: pulldown</span><span lang="" class="or-hint active">Showing a pull-down list of options (type=select_one list, appearance=minimal)</span><select name="/widgets/select_widgets/select1_spinner" data-name="/widgets/select_widgets/select1_spinner" data-type-xml="select1"><option value="">...</option><option value="a">option a</option><option value="b">option b</option><option value="c">option c</option><option value="d">option d</option></select><span class="or-option-translations" style="display:none;">
//                 </span></label><label class="question or-appearance-autocomplete "><span lang="" class="question-label active">Select one autocomplete widget</span><span lang="" class="or-hint active"><p>Type e.g. 'g' to filter options.</p>(type=select_one, appearance=autocomplete)</span><input name="/widgets/select_widgets/select1_autocomplete" data-name="/widgets/select_widgets/select1_autocomplete" data-type-xml="select1" type="text" list="widgetsselectwidgetsselect1autocomplete"/><datalist id="widgetsselectwidgetsselect1autocomplete"><option value="">...</option><option value="king">kingfisher</option><option value="pig">pigeon</option><option value="nut">nuthatch</option></datalist><span class="or-option-translations" style="display:none;">
//                 </span></label><fieldset class="question or-appearance-compact "><fieldset><legend><span lang="" class="question-label active">Grid select one widget</span><span lang="" class="or-hint active">Make sure to put a.jpg and b.jpg in the form-media folder to see images here. (type=select<em>one a</em>b, appearance=compact)</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="radio" name="/widgets/select_widgets/grid_test" data-name="/widgets/select_widgets/grid_test" value="a" data-type-xml="select1"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/a.jpg" data-itext-id="/widgets/select_widgets/grid_test/a:label" alt="image"/></label><label class=""><input type="radio" name="/widgets/select_widgets/grid_test" data-name="/widgets/select_widgets/grid_test" value="b" data-type-xml="select1"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/b.jpg" data-itext-id="/widgets/select_widgets/grid_test/b:label" alt="image"/></label></div></fieldset></fieldset><fieldset class="question or-appearance-compact-2 "><fieldset><legend><span lang="" class="question-label active">Grid select one widget</span><span lang="" class="or-hint active">Grid with a maximum of 2 columns. (type=select<em>one a</em>b, appearance=compact-2)</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="radio" name="/widgets/select_widgets/grid_2_columns" data-name="/widgets/select_widgets/grid_2_columns" value="a" data-type-xml="select1"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/a.jpg" data-itext-id="/widgets/select_widgets/grid_2_columns/a:label" alt="image"/></label><label class=""><input type="radio" name="/widgets/select_widgets/grid_2_columns" data-name="/widgets/select_widgets/grid_2_columns" value="b" data-type-xml="select1"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/b.jpg" data-itext-id="/widgets/select_widgets/grid_2_columns/b:label" alt="image"/></label><label class=""><input type="radio" name="/widgets/select_widgets/grid_2_columns" data-name="/widgets/select_widgets/grid_2_columns" value="c" data-type-xml="select1"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/c.jpg" data-itext-id="/widgets/select_widgets/grid_2_columns/c:label" alt="image"/></label><label class=""><input type="radio" name="/widgets/select_widgets/grid_2_columns" data-name="/widgets/select_widgets/grid_2_columns" value="d" data-type-xml="select1"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/d.jpg" data-itext-id="/widgets/select_widgets/grid_2_columns/d:label" alt="image"/></label></div></fieldset></fieldset><section class="or-group or-appearance-field-list " name="/widgets/select_widgets/table_list_test"><h4><span lang="" class="question-label active">Table</span></h4><fieldset class="question or-appearance-label "><fieldset><legend><span lang="" class="question-label active">Table</span><span lang="" class="or-hint active">Show only the labels of these options and not the inputs (type=select<em>one yes</em>no, appearance=label)</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test/table_list_test_label" data-name="/widgets/select_widgets/table_list_test/table_list_test_label" value="yes" data-type-xml="select1"/><span lang="" class="option-label active">Yes</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test/table_list_test_label" data-name="/widgets/select_widgets/table_list_test/table_list_test_label" value="no" data-type-xml="select1"/><span lang="" class="option-label active">No</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test/table_list_test_label" data-name="/widgets/select_widgets/table_list_test/table_list_test_label" value="dk" data-type-xml="select1"/><span lang="" class="option-label active">Don't Know</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test/table_list_test_label" data-name="/widgets/select_widgets/table_list_test/table_list_test_label" value="na" data-type-xml="select1"/><span lang="" class="option-label active">Not Applicable</span></label></div></fieldset></fieldset><fieldset class="question or-appearance-list-nolabel "><fieldset><legend><span lang="" class="question-label active">Q1</span><span lang="" class="or-hint active">Show only the inputs of these options and not the labels (type=select<em>one yes</em>no, appearance=list-nolabel)</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test/table_list_1" data-name="/widgets/select_widgets/table_list_test/table_list_1" value="yes" data-type-xml="select1"/><span lang="" class="option-label active">Yes</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test/table_list_1" data-name="/widgets/select_widgets/table_list_test/table_list_1" value="no" data-type-xml="select1"/><span lang="" class="option-label active">No</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test/table_list_1" data-name="/widgets/select_widgets/table_list_test/table_list_1" value="dk" data-type-xml="select1"/><span lang="" class="option-label active">Don't Know</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test/table_list_1" data-name="/widgets/select_widgets/table_list_test/table_list_1" value="na" data-type-xml="select1"/><span lang="" class="option-label active">Not Applicable</span></label></div></fieldset></fieldset><fieldset class="question or-appearance-list-nolabel "><fieldset><legend><span lang="" class="question-label active">Question 2</span><span lang="" class="or-hint active">Show only the inputs of these options and not the labels (type=select<em>one yes</em>no, appearance=list-nolabel)</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test/table_list_2" data-name="/widgets/select_widgets/table_list_test/table_list_2" value="yes" data-type-xml="select1"/><span lang="" class="option-label active">Yes</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test/table_list_2" data-name="/widgets/select_widgets/table_list_test/table_list_2" value="no" data-type-xml="select1"/><span lang="" class="option-label active">No</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test/table_list_2" data-name="/widgets/select_widgets/table_list_test/table_list_2" value="dk" data-type-xml="select1"/><span lang="" class="option-label active">Don't Know</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test/table_list_2" data-name="/widgets/select_widgets/table_list_test/table_list_2" value="na" data-type-xml="select1"/><span lang="" class="option-label active">Not Applicable</span></label></div></fieldset></fieldset>
//             </section><!--end of group --><section class="or-group-data or-appearance-field-list " name="/widgets/select_widgets/table_list_test2"><label class="question note non-select "><span lang="" class="question-label active">Table (alternative method)</span><span lang="" class="or-hint active">An alternative way to do almost the same (appearance=table-list) but it will look a bit different.</span><input type="text" name="/widgets/select_widgets/table_list_test2/generated_table_list_label_37" data-type-xml="string" readonly="readonly"/></label><fieldset class="question or-appearance-label "><fieldset><legend>
//                     </legend><div class="option-wrapper"><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test2/reserved_name_for_field_list_labels_38" data-name="/widgets/select_widgets/table_list_test2/reserved_name_for_field_list_labels_38" value="yes" data-type-xml="select1"/><span lang="" class="option-label active">Yes</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test2/reserved_name_for_field_list_labels_38" data-name="/widgets/select_widgets/table_list_test2/reserved_name_for_field_list_labels_38" value="no" data-type-xml="select1"/><span lang="" class="option-label active">No</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test2/reserved_name_for_field_list_labels_38" data-name="/widgets/select_widgets/table_list_test2/reserved_name_for_field_list_labels_38" value="dk" data-type-xml="select1"/><span lang="" class="option-label active">Don't Know</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test2/reserved_name_for_field_list_labels_38" data-name="/widgets/select_widgets/table_list_test2/reserved_name_for_field_list_labels_38" value="na" data-type-xml="select1"/><span lang="" class="option-label active">Not Applicable</span></label></div></fieldset></fieldset><fieldset class="question or-appearance-list-nolabel "><fieldset><legend><span lang="" class="question-label active">Q1</span><span lang="" class="or-hint active">No need to do anything special here</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test2/table_list_3" data-name="/widgets/select_widgets/table_list_test2/table_list_3" value="yes" data-type-xml="select1"/><span lang="" class="option-label active">Yes</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test2/table_list_3" data-name="/widgets/select_widgets/table_list_test2/table_list_3" value="no" data-type-xml="select1"/><span lang="" class="option-label active">No</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test2/table_list_3" data-name="/widgets/select_widgets/table_list_test2/table_list_3" value="dk" data-type-xml="select1"/><span lang="" class="option-label active">Don't Know</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test2/table_list_3" data-name="/widgets/select_widgets/table_list_test2/table_list_3" value="na" data-type-xml="select1"/><span lang="" class="option-label active">Not Applicable</span></label></div></fieldset></fieldset><fieldset class="question or-appearance-list-nolabel "><fieldset><legend><span lang="" class="question-label active">Question 2</span><span lang="" class="or-hint active">No need to do anything special here</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test2/table_list_4" data-name="/widgets/select_widgets/table_list_test2/table_list_4" value="yes" data-type-xml="select1"/><span lang="" class="option-label active">Yes</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test2/table_list_4" data-name="/widgets/select_widgets/table_list_test2/table_list_4" value="no" data-type-xml="select1"/><span lang="" class="option-label active">No</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test2/table_list_4" data-name="/widgets/select_widgets/table_list_test2/table_list_4" value="dk" data-type-xml="select1"/><span lang="" class="option-label active">Don't Know</span></label><label class=""><input type="radio" name="/widgets/select_widgets/table_list_test2/table_list_4" data-name="/widgets/select_widgets/table_list_test2/table_list_4" value="na" data-type-xml="select1"/><span lang="" class="option-label active">Not Applicable</span></label></div></fieldset></fieldset>
//             </section><!--end of group --><section class="or-group or-appearance-field-list " name="/widgets/select_widgets/happy_sad_table_2"><h4><span lang="" class="question-label active">Table with image labels</span></h4><fieldset class="question or-appearance-label "><fieldset><legend><span lang="" class="question-label active">Select mood</span><span lang="" class="or-hint active">Show only the labels of these options and not the inputs (type=select<em>one yes</em>no, appearance=label)</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="checkbox" name="/widgets/select_widgets/happy_sad_table_2/happy_sad_second_method" value="happy" data-type-xml="select"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/happy.jpg" data-itext-id="/widgets/select_widgets/happy_sad_table_2/happy_sad_second_method/happy:label" alt="image"/></label><label class=""><input type="checkbox" name="/widgets/select_widgets/happy_sad_table_2/happy_sad_second_method" value="sad" data-type-xml="select"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/sad.jpg" data-itext-id="/widgets/select_widgets/happy_sad_table_2/happy_sad_second_method/sad:label" alt="image"/></label></div></fieldset></fieldset><fieldset class="question or-appearance-list-nolabel "><fieldset><legend><span lang="" class="question-label active">Brian</span><span lang="" class="or-hint active">Show only the inputs of these options and not the labels (type=select<em>one yes</em>no, appearance=list-nolabel)</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="checkbox" name="/widgets/select_widgets/happy_sad_table_2/happy_sad_brian2" value="happy" data-type-xml="select"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/happy.jpg" data-itext-id="/widgets/select_widgets/happy_sad_table_2/happy_sad_brian2/happy:label" alt="image"/></label><label class=""><input type="checkbox" name="/widgets/select_widgets/happy_sad_table_2/happy_sad_brian2" value="sad" data-type-xml="select"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/sad.jpg" data-itext-id="/widgets/select_widgets/happy_sad_table_2/happy_sad_brian2/sad:label" alt="image"/></label></div></fieldset></fieldset><fieldset class="question or-appearance-list-nolabel "><fieldset><legend><span lang="" class="question-label active">Michael</span><span lang="" class="or-hint active">Show only the inputs of these options and not the labels (type=select<em>one yes</em>no, appearance=list-nolabel)</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="checkbox" name="/widgets/select_widgets/happy_sad_table_2/happy_sad_michael2" value="happy" data-type-xml="select"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/happy.jpg" data-itext-id="/widgets/select_widgets/happy_sad_table_2/happy_sad_michael2/happy:label" alt="image"/></label><label class=""><input type="checkbox" name="/widgets/select_widgets/happy_sad_table_2/happy_sad_michael2" value="sad" data-type-xml="select"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/sad.jpg" data-itext-id="/widgets/select_widgets/happy_sad_table_2/happy_sad_michael2/sad:label" alt="image"/></label></div></fieldset></fieldset>
//             </section><!--end of group --><section class="or-group-data or-appearance-field-list " name="/widgets/select_widgets/happy_sad_table"><label class="question note non-select "><span lang="" class="question-label active">Table with image labels (alternative method)</span><span lang="" class="or-hint active">An alternative way to do the same (appearance=table-list) but it will look a bit different.</span><input type="text" name="/widgets/select_widgets/happy_sad_table/generated_table_list_label_46" data-type-xml="string" readonly="readonly"/></label><fieldset class="question or-appearance-label "><fieldset><legend>
//                     </legend><div class="option-wrapper"><label class=""><input type="checkbox" name="/widgets/select_widgets/happy_sad_table/reserved_name_for_field_list_labels_47" value="happy" data-type-xml="select"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/happy.jpg" data-itext-id="/widgets/select_widgets/happy_sad_table/reserved_name_for_field_list_labels_47/happy:label" alt="image"/></label><label class=""><input type="checkbox" name="/widgets/select_widgets/happy_sad_table/reserved_name_for_field_list_labels_47" value="sad" data-type-xml="select"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/sad.jpg" data-itext-id="/widgets/select_widgets/happy_sad_table/reserved_name_for_field_list_labels_47/sad:label" alt="image"/></label></div></fieldset></fieldset><fieldset class="question or-appearance-list-nolabel "><fieldset><legend><span lang="" class="question-label active">Brian</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="checkbox" name="/widgets/select_widgets/happy_sad_table/happy_sad_brian" value="happy" data-type-xml="select"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/happy.jpg" data-itext-id="/widgets/select_widgets/happy_sad_table/happy_sad_brian/happy:label" alt="image"/></label><label class=""><input type="checkbox" name="/widgets/select_widgets/happy_sad_table/happy_sad_brian" value="sad" data-type-xml="select"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/sad.jpg" data-itext-id="/widgets/select_widgets/happy_sad_table/happy_sad_brian/sad:label" alt="image"/></label></div></fieldset></fieldset><fieldset class="question or-appearance-list-nolabel "><fieldset><legend><span lang="" class="question-label active">Michael</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="checkbox" name="/widgets/select_widgets/happy_sad_table/happy_sad_michael" value="happy" data-type-xml="select"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/happy.jpg" data-itext-id="/widgets/select_widgets/happy_sad_table/happy_sad_michael/happy:label" alt="image"/></label><label class=""><input type="checkbox" name="/widgets/select_widgets/happy_sad_table/happy_sad_michael" value="sad" data-type-xml="select"/><span lang="default" class="option-label active">
//                  </span><img lang="default" class="active" src="jr://images/sad.jpg" data-itext-id="/widgets/select_widgets/happy_sad_table/happy_sad_michael/sad:label" alt="image"/></label></div></fieldset></fieldset>
//             </section><!--end of group -->
//             </section><!--end of group -->
//     <section class="or-group " name="/widgets/cascading_widgets"><h4><span lang="" class="question-label active">Cascading Select widgets</span></h4><section class="or-group " name="/widgets/cascading_widgets/group1"><h4><span lang="" class="question-label active">Cascading Selects with Radio Buttons</span></h4><fieldset class="question simple-select "><fieldset><legend><span lang="" class="question-label active">Country</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="radio" name="/widgets/cascading_widgets/group1/country" data-name="/widgets/cascading_widgets/group1/country" value="nl" data-type-xml="select1"/><span lang="" class="option-label active">The Netherlands</span></label><label class=""><input type="radio" name="/widgets/cascading_widgets/group1/country" data-name="/widgets/cascading_widgets/group1/country" value="usa" data-type-xml="select1"/><span lang="" class="option-label active">United States</span></label></div></fieldset></fieldset><fieldset class="question simple-select "><fieldset><legend><span lang="" class="question-label active">City</span><span lang="" class="or-hint active"> Using a choice filter to update options based on a previous answer (choice_filter: country = <span class="or-output" data-value=" /widgets/cascading_widgets/group1/country "> </span>)  </span>
//                     </legend><div class="option-wrapper"><label class="itemset-template" data-items-path="instance('cities')/root/item[country= /widgets/cascading_widgets/group1/country ]"><input type="radio" name="/widgets/cascading_widgets/group1/city" data-name="/widgets/cascading_widgets/group1/city" data-type-xml="select1" value=""/></label><span class="itemset-labels" data-value-ref="name" data-label-type="itext" data-label-ref="itextId"><span lang="default" class="option-label active" data-itext-id="static_instance-cities-0">Amsterdam</span><span lang="default" class="option-label active" data-itext-id="static_instance-cities-1">Denver</span><span lang="default" class="option-label active" data-itext-id="static_instance-cities-2">New York City</span><span lang="default" class="option-label active" data-itext-id="static_instance-cities-3">Los Angeles</span><span lang="default" class="option-label active" data-itext-id="static_instance-cities-4">Rotterdam</span><span lang="default" class="option-label active" data-itext-id="static_instance-cities-5">Dronten</span>
//             </span></div></fieldset></fieldset><fieldset class="question simple-select "><fieldset><legend><span lang="" class="question-label active">Neighborhood</span><span lang="" class="or-hint active"> Using a choice filter to update options based on previous answers (choice_filter: country = <span class="or-output" data-value=" /widgets/cascading_widgets/group1/country "> </span> and city = <span class="or-output" data-value=" /widgets/cascading_widgets/group1/city "> </span>)  </span>
//                     </legend><div class="option-wrapper"><label class="itemset-template" data-items-path="instance('neighborhoods')/root/item[country= /widgets/cascading_widgets/group1/country  and city= /widgets/cascading_widgets/group1/city ]"><input type="radio" name="/widgets/cascading_widgets/group1/neighborhood" data-name="/widgets/cascading_widgets/group1/neighborhood" data-type-xml="select1" value=""/></label><span class="itemset-labels" data-value-ref="name" data-label-type="itext" data-label-ref="itextId"><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-0">Bronx</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-1">Harlem</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-2">Bel Air</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-3">Westerpark</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-4">Park Hill</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-5">Harbor</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-6">Dam</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-7">Downtown</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-8">Harbor</span>
//             </span></div></fieldset></fieldset>
//             </section><!--end of group --><section class="or-group " name="/widgets/cascading_widgets/group2"><h4><span lang="" class="question-label active">Cascading Selects with Pulldowns</span></h4><label class="question or-appearance-minimal "><span lang="" class="question-label active">Country</span><span lang="" class="or-hint active">(appearance: minimal)</span><select name="/widgets/cascading_widgets/group2/country2" data-name="/widgets/cascading_widgets/group2/country2" data-type-xml="select1"><option value="">...</option><option value="nl">The Netherlands</option><option value="usa">United States</option></select><span class="or-option-translations" style="display:none;">
//                 </span></label><label class="question or-appearance-minimal "><span lang="" class="question-label active">City</span><span lang="" class="or-hint active"> Using a choice filter to update options based on a previous answer (choice_filter: country = <span class="or-output" data-value=" /widgets/cascading_widgets/group2/country2 "> </span>, appearance: minimal)  </span><select name="/widgets/cascading_widgets/group2/city2" data-name="/widgets/cascading_widgets/group2/city2" data-type-xml="select1"><option class="itemset-template" value="" data-items-path="instance('cities')/root/item[country= /widgets/cascading_widgets/group2/country2 ]">...</option></select><span class="or-option-translations" style="display:none;">
//                 </span><span class="itemset-labels" data-value-ref="name" data-label-type="itext" data-label-ref="itextId"><span lang="default" class="option-label active" data-itext-id="static_instance-cities-0">Amsterdam</span><span lang="default" class="option-label active" data-itext-id="static_instance-cities-1">Denver</span><span lang="default" class="option-label active" data-itext-id="static_instance-cities-2">New York City</span><span lang="default" class="option-label active" data-itext-id="static_instance-cities-3">Los Angeles</span><span lang="default" class="option-label active" data-itext-id="static_instance-cities-4">Rotterdam</span><span lang="default" class="option-label active" data-itext-id="static_instance-cities-5">Dronten</span>
//             </span></label><label class="question or-appearance-minimal "><span lang="" class="question-label active">Neighborhood</span><span lang="" class="or-hint active"> Using a choice filter to update options based on previous answers (choice_filter: country = <span class="or-output" data-value=" /widgets/cascading_widgets/group2/country2 "> </span> and city = <span class="or-output" data-value=" /widgets/cascading_widgets/group2/city2 "> </span>, appearance = minimal)  </span><select name="/widgets/cascading_widgets/group2/neighborhood2" data-name="/widgets/cascading_widgets/group2/neighborhood2" data-type-xml="select1"><option class="itemset-template" value="" data-items-path="instance('neighborhoods')/root/item[country= /widgets/cascading_widgets/group2/country2  and city= /widgets/cascading_widgets/group2/city2 ]">...</option></select><span class="or-option-translations" style="display:none;">
//                 </span><span class="itemset-labels" data-value-ref="name" data-label-type="itext" data-label-ref="itextId"><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-0">Bronx</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-1">Harlem</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-2">Bel Air</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-3">Westerpark</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-4">Park Hill</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-5">Harbor</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-6">Dam</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-7">Downtown</span><span lang="default" class="option-label active" data-itext-id="static_instance-neighborhoods-8">Harbor</span>
//             </span></label>
//             </section><!--end of group -->
//             </section><!--end of group -->
//     <section class="or-group " name="/widgets/geopoint_widgets"><h4><span lang="" class="question-label active">Geo widgets</span></h4><label class="question non-select "><span lang="" class="question-label active">Geopoint widget</span><span lang="" class="or-hint active">Record the gps location. In enketo it also shows a map. (type=geopoint)</span><input type="text" name="/widgets/geopoint_widgets/geopoint" data-type-xml="geopoint"/></label><label class="question non-select or-appearance-maps "><span lang="" class="question-label active">Geopoint with map Widget</span><span lang="" class="or-hint active">Record the gps location. In enketo is is the same as the previous. (type=geopoint, appearance=maps)</span><input type="text" name="/widgets/geopoint_widgets/geopoint_m" data-type-xml="geopoint"/></label><label class="question non-select or-appearance-maps or-appearance-hide-input "><span lang="" class="question-label active">Geopoint widget that hides input fields by default</span><span lang="" class="or-hint active">Show a larger map (on desktop screens), you can hide the input fields. (appearance = hide-input)</span><input type="text" name="/widgets/geopoint_widgets/geopoint_hide" data-type-xml="geopoint"/></label><label class="question non-select or-appearance-maps or-appearance-hide-input "><span lang="" class="question-label active">Geotrace widget</span><span lang="" class="or-hint active">Record a sequence of geopoints (type=geotrace, appearance=maps hide-input)</span><input type="text" name="/widgets/geopoint_widgets/geotrace" data-type-xml="geotrace"/></label><label class="question non-select or-appearance-maps or-appearance-hide-input "><span lang="" class="question-label active">Geoshape widget</span><span lang="" class="or-hint active">Record a closed sequence/polygon of geopoints (type=geoshape, appearance=maps hide-input)</span><input type="text" name="/widgets/geopoint_widgets/geoshape" data-type-xml="geoshape"/></label>
//             </section><!--end of group -->
//     <section class="or-group " name="/widgets/media_widgets"><h4><span lang="" class="question-label active">Media input widgets</span></h4><label class="question non-select "><span lang="" class="question-label active">Image widget</span><span lang="" class="or-hint active">Select an image or take a photo (type=image)</span><input type="file" name="/widgets/media_widgets/image" data-type-xml="binary" accept="image/*"/></label><label class="question non-select or-appearance-draw "><span lang="" class="question-label active">Draw widget</span><span lang="" class="or-hint active">Make a drawing (type=image, appearance=draw)</span><input type="file" name="/widgets/media_widgets/draw" data-type-xml="binary" accept="image/*"/></label><label class="question non-select or-appearance-signature "><span lang="" class="question-label active">Signature widget</span><span lang="" class="or-hint active">Add a signature (type=image, appearance=signature)</span><input type="file" name="/widgets/media_widgets/signature" data-type-xml="binary" accept="image/*"/></label><label class="question non-select or-appearance-annotate "><span lang="" class="question-label active">Annotate image widget</span><span lang="" class="or-hint active">Upload and annotate an image (type=image, appearance=annotate)</span><input type="file" name="/widgets/media_widgets/annotate" data-type-xml="binary" accept="image/*"/></label><label class="question non-select "><span lang="" class="question-label active">Audio widget</span><span lang="" class="or-hint active">Select an audio file or record audio (type=audio)</span><input type="file" name="/widgets/media_widgets/my_audio" data-type-xml="binary" accept="audio/*"/></label><label class="question non-select "><span lang="" class="question-label active">Video widget</span><span lang="" class="or-hint active">Select a video file or record a video (type=video)</span><input type="file" name="/widgets/media_widgets/my_video" data-type-xml="binary" accept="video/*"/></label><label class="question non-select "><span lang="" class="question-label active">Barcode widget</span><span lang="" class="or-hint active">Scans multi-format 1d/2d barcodes. In enketo it allows manual entry (type=barcode)</span><input type="text" name="/widgets/media_widgets/my_barcode" data-type-xml="barcode"/></label>
//             </section><!--end of group -->
//     <section class="or-group " name="/widgets/display_widgets"><h4><span lang="" class="question-label active">Display widgets</span></h4><label class="question note non-select "><span lang="" class="question-label active"><p>Note widget. In notes you can emphasize <em>words</em> or <em>multiple words</em> or <strong>strongly emphasize something</strong>.</p><p>You can also use a line break to start a new sentence.</p>
// The decimal number you entered was <span class="or-output" data-value=" /widgets/number_widgets/decimal "> </span>.  </span><span lang="" class="or-hint active">This is a note and it uses a value of another field in its label (type=note)</span><input type="text" name="/widgets/display_widgets/my_output" data-type-xml="string" readonly="readonly"/></label><label class="question non-select "><span lang="default" class="question-label active" data-itext-id="/widgets/display_widgets/text_media:label">You can add a sound recording, an image and a video to any input label or to a note.</span><audio controls="controls" lang="default" class="active" src="jr://audio/goldeneagle.mp3" data-itext-id="/widgets/display_widgets/text_media:label">Your browser does not support HTML5 audio.</audio><span lang="" class="or-hint active">Add the file name in the audio column on your survey sheet. Make sure you upload this file when you publish your form.</span><input type="text" name="/widgets/display_widgets/text_media" data-type-xml="string"/></label><fieldset class="question simple-select "><fieldset><legend><span lang="" class="question-label active">You can also add media to choices. Choose your favorite bird.</span><span lang="" class="or-hint active">Add the file name in the image column on your choices sheet. Make sure you upload this file when you publish your form.</span>
//                     </legend><div class="option-wrapper"><label class=""><input type="radio" name="/widgets/display_widgets/select_media" data-name="/widgets/display_widgets/select_media" value="king" data-type-xml="select1"/><span lang="default" class="option-label active" data-itext-id="/widgets/display_widgets/select_media/king:label">kingfisher</span><img lang="default" class="active" src="jr://images/kingfisher.png" data-itext-id="/widgets/display_widgets/select_media/king:label" alt="image"/></label><label class=""><input type="radio" name="/widgets/display_widgets/select_media" data-name="/widgets/display_widgets/select_media" value="pig" data-type-xml="select1"/><span lang="default" class="option-label active" data-itext-id="/widgets/display_widgets/select_media/pig:label">pigeon</span><img lang="default" class="active" src="jr://images/pigeon.png" data-itext-id="/widgets/display_widgets/select_media/pig:label" alt="image"/></label><label class=""><input type="radio" name="/widgets/display_widgets/select_media" data-name="/widgets/display_widgets/select_media" value="nut" data-type-xml="select1"/><span lang="default" class="option-label active" data-itext-id="/widgets/display_widgets/select_media/nut:label">nuthatch</span><img lang="default" class="active" src="jr://images/nuthatch.png" data-itext-id="/widgets/display_widgets/select_media/nut:label" alt="image"/></label></div></fieldset></fieldset><fieldset class="question simple-select trigger "><fieldset><legend><span lang="" class="question-label active">Acknowledge widget</span><span class="required">*</span><span lang="" class="or-hint active">Prompts for confirmation. Useful to combine with required or relevant. (type=trigger)</span>
//                     </legend><div class="option-wrapper"><label><input value="OK" type="radio" name="/widgets/display_widgets/my_trigger" data-name="/widgets/display_widgets/my_trigger" data-required="true()" data-type-xml="string"/><span class="option-label active" lang="">OK</span></label></div></fieldset><span class="or-required-msg active" lang="" data-i18n="constraint.required">This field is required</span></fieldset>
//             </section><!--end of group -->

// <fieldset id="or-calculated-items" style="display:none;"><label class="calculation non-select "><input type="hidden" name="/widgets/meta/instanceID" data-calculate="concat('uuid:', uuid())" data-type-xml="string"/></label><label class="calculation non-select "><input type="hidden" name="/widgets/formhub/uuid" data-calculate="'01a710c316b44364986eb020e7fc7457'" data-type-xml="string"/></label></fieldset></form>
// `


function initializeForm (formHTML, model) {
  const formHTMLDecoded = $('<textarea />').html(formHTML).text()
  const modelDecoded = $('<textarea />').html(model).text()
  $( '.form-header' ).after(formHTMLDecoded);
  form = new Form( 'form.or:eq(0)', {
    modelStr: modelDecoded
  }, {
    arcGis: {
      basemaps: [ "streets", "topo", "satellite", "osm" ],
      webMapId: 'f2e9b762544945f390ca4ac3671cfa72',
      hasZ: true
    },
    'clearIrrelevantImmediately': true,
    'goTo': true
  } );
  // for debugging
  window.form = form;
  //initialize form and check for load errors
  loadErrors = form.init();
  if ( loadErrors.length > 0 ) {
    window.alert( 'loadErrors: ' + loadErrors.join( ', ' ) );
  }
}

if (window.form) {
  initializeForm(window.form, window.model)
} else {
  $('.main').after('<h1>No xform specified!</h1>')
}
