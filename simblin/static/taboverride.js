/*!
 * Tab Override jQuery Plugin v1.0
 * http://wjbryant.com/projects/tab-override/
 *
 * Copyright (c) 2010 Bill Bryant
 * Licensed under the MIT license
 * http://opensource.org/licenses/mit-license.php
 */

jQuery.fn.tabOverride = (function ($) {
    var aTab = '\t';
    
    function overrideKeyDown(e) {
        var tab, // the string representing a tab
            tabLen, // the length of a tab
            text, // initial text in the textarea
            range, // the IE TextRange object
            tempRange, // used to calculate selection start and end positions in IE
            preNewlines, // the number of newline (\r\n) characters before the selection start (for IE)
            selNewlines, // the number of newline (\r\n) characters within the selection (for IE)
            initScrollTop, // initial scrollTop value to fix scrolling in Firefox
            selStart, // the selection start position
            selEnd, // the selection end position
            sel, // the selected text
            startLine, // for multi-line selections, the first character position of the first line
            endLine, // for multi-line selections, the last character position of the last line
            numTabs, // the number of tabs inserted / removed in the selection
            startTab, // if a tab was removed from the start of the first line
            preTab; // if a tab was removed before the start of the selection
        
        // tab key - insert / remove tab
        if (e.keyCode === 9) {
            
            // initialize variables
            tab = aTab;
            tabLen = tab.length;
            text = this.value;
            initScrollTop = this.scrollTop; // scrollTop is supported by all modern browsers
            numTabs = 0;
            startTab = 0;
            preTab = 0;
            
            if (typeof this.selectionStart !== 'undefined') {
                selStart = this.selectionStart;
                selEnd = this.selectionEnd;
                sel = text.slice(selStart, selEnd);
            } else if (document.selection) { // IE
                range = document.selection.createRange();
                sel = range.text;
                tempRange = range.duplicate();
                tempRange.moveToElementText(this);
                tempRange.setEndPoint('EndToEnd', range);
                selEnd = tempRange.text.length;
                selStart = selEnd - sel.length;
                // whenever the value of the textarea is changed, the range needs to be reset
                // IE (and Opera) use both \r and \n for newlines - this adds an extra character
                // that needs to be accounted for when doing position calculations
                // these values are used to offset the selection start and end positions
                preNewlines = text.slice(0, selStart).split('\r\n').length - 1;
                selNewlines = sel.split('\r\n').length - 1;
            } else {
                // cannot access textarea selection - do nothing
                return;
            }
            
            // multi-line selection
            if (selStart !== selEnd && sel.indexOf('\n') !== -1) {
                // for multiple lines, only insert / remove tabs from the beginning of each line
                
                // find the start of the first selected line
                if (selStart === 0 || text.charAt(selStart - 1) === '\n') {
                    // the selection starts at the beginning of a line
                    startLine = selStart;
                } else {
                    // the selection starts after the beginning of a line
                    // set startLine to the beginning of the first partially selected line
                    // subtract 1 from selStart in case the cursor is at the newline character,
                    // for instance, if the very end of the previous line was selected
                    // add 1 to get the next character after the newline
                    // if there is none before the selection, lastIndexOf returns -1
                    // when 1 is added to that it becomes 0 and the first character is used
                    startLine = text.lastIndexOf('\n', selStart - 1) + 1;
                }
                
                // find the end of the last selected line
                if (selEnd === text.length || text.charAt(selEnd) === '\n') {
                    // the selection ends at the end of a line
                    endLine = selEnd;
                } else {
                    // the selection ends before the end of a line
                    // set endLine to the end of the last partially selected line
                    endLine = text.indexOf('\n', selEnd);
                    if (endLine === -1) {
                        endLine = text.length;
                    }
                }
                
                // if the shift key was pressed, remove tabs instead of inserting them
                if (e.shiftKey) {
                    if (text.slice(startLine).indexOf(tab) === 0) {
                        // is this tab part of the selection?
                        if (startLine === selStart) {
                            // it is, remove it
                            sel = sel.slice(tabLen);
                        } else {
                            // the tab comes before the selection
                            preTab = tabLen;
                        }
                        startTab = tabLen;
                    }
                    
                    this.value = text.slice(0, startLine) + text.slice(startLine + preTab, selStart) +
                        sel.replace(new RegExp('\n' + tab, 'g'), function () {
                            numTabs += 1;
                            return '\n';
                        }) + text.slice(selEnd);
                    
                    // set start and end points
                    if (range) { // IE
                        // setting end first makes calculations easier
                        range.collapse();
                        range.moveEnd('character', selEnd - startTab - (numTabs * tabLen) - selNewlines - preNewlines);
                        range.moveStart('character', selStart - preTab - preNewlines);
                        range.select();
                    } else {
                        // set start first for Opera
                        this.selectionStart = selStart - preTab; // preTab is 0 or tabLen
                        // move the selection end over by the total number of tabs removed
                        this.selectionEnd = selEnd - startTab - (numTabs * tabLen);
                    }
                } else { // no shift key
                    numTabs = 1; // for the first tab
                    // insert tabs at the beginning of each line of the selection
                    this.value = text.slice(0, startLine) + tab + text.slice(startLine, selStart) +
                        sel.replace(/\n/g, function () {
                            numTabs += 1;
                            return '\n' + tab;
                        }) + text.slice(selEnd);
                    
                    // set start and end points
                    if (range) { // IE
                        range.collapse();
                        range.moveEnd('character', selEnd + (numTabs * tabLen) - selNewlines - preNewlines);
                        range.moveStart('character', selStart + tabLen - preNewlines);
                        range.select();
                    } else {
                        // the selection start is always moved by 1 character
                        this.selectionStart = selStart + tabLen;
                        // move the selection end over by the total number of tabs inserted
                        this.selectionEnd = selEnd + (numTabs * tabLen);
                    }
                }
            } else { // single line selection
                // if the shift key was pressed, remove a tab instead of inserting one
                if (e.shiftKey) {
                    // if the character before the selection is a tab, remove it
                    if (text.slice(selStart - tabLen).indexOf(tab) === 0) {
                        this.value = text.slice(0, selStart - tabLen) + text.slice(selStart);
                        
                        // set start and end points
                        if (range) { // IE
                            // collapses range and moves it by -1 tab
                            range.move('character', selStart - tabLen - preNewlines);
                            range.select();
                        } else {
                            this.selectionEnd = this.selectionStart = selStart - tabLen;
                        }
                    }
                } else { // no shift key - insert a tab
                    if (range) { // IE
                        // if no text is selected and the cursor is at the beginning of a line
                        // (except the first line), IE places the cursor at the carriage return character
                        // the tab must be placed after the \r\n pair
                        if (text.charAt(selStart) === '\r') {
                            this.value = text.slice(0, selStart + 2) + tab + text.slice(selEnd + 2);
                            // collapse the range and move it to the appropriate location
                            range.move('character', selStart + 1 + tabLen - preNewlines);
                        } else {
                            this.value = text.slice(0, selStart) + tab + text.slice(selEnd);
                            // collapse the range and move it to the appropriate location
                            range.move('character', selStart + tabLen - preNewlines);
                        }
                        range.select();
                    } else {
                        this.value = text.slice(0, selStart) + tab + text.slice(selEnd);
                        this.selectionEnd = this.selectionStart = selStart + tabLen;
                    }
                }
            }
            
            // this is really just for Firefox, but will be executed by all browsers
            // whenever the textarea value property is reset, Firefox scrolls back to the top
            // this will reset it to the original scroll value
            this.scrollTop = initScrollTop;
            
            e.preventDefault();
        }
    }
    
    // Opera (and Firefox) also fire a keypress event when the tab key is pressed
    // Opera requires that the default action be prevented on this event, or the
    // textarea will lose focus
    function overrideKeyPress(e) {
        if (e.keyCode === 9) {
            e.preventDefault();
        }
    }
    
    // the tabOverride method
    // tabs will be overriden if enable is true (default)
    function tabOverride(enable) {
        // unbind the tab override functions so they are not bound more than once
        this.each(function () {
            $(this).unbind('.tabOverride');
        });
        
        // only bind the tab override functions if the enable argument is truthy or not specified
        if (enable || typeof enable === 'undefined') {
            this.each(function () {
                if (this.nodeName && this.nodeName.toLowerCase() === 'textarea') {
                    $(this).bind('keydown.tabOverride', overrideKeyDown).bind('keypress.tabOverride', overrideKeyPress);
                }
            });
        }
        
        // always return the jQuery object
        return $(this);
    }
    
    tabOverride.getTabSize = function () {
        return aTab === '\t' ? 0 : aTab.length;
    };
    
    tabOverride.setTabSize = function (size) {
        var i;
        if (!size) {
            aTab = '\t';
        } else if (typeof size === 'number' && size > 0) {
            aTab = '';
            for (i = 0; i < size; i += 1) {
                aTab += ' ';
            }
        }
    };
    
    return tabOverride;
}(jQuery));