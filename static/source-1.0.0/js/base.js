
/***************************************** FUNCTIONS *****************************************/


function drawRing(canvas, color, value){
    var ctx = canvas.getContext('2d');
    /*Draw text*/
    ctx.textAlign = 'center';
    ctx. textBaseline = 'middle';
    ctx.fillStyle = "white";
    ctx.font = "80px Arial";
    ctx.fillText(String(value), (canvas.width / 2), (canvas.height / 2));
    /*Draw ring*/
    ctx.beginPath()
    ctx.arc(Math.floor(canvas.width / 2),Math.floor(canvas.height / 2),(canvas.height / 2),0,Math.PI*2, false); // outer (filled)
    ctx.arc(Math.floor(canvas.width / 2),Math.floor(canvas.height / 2),(canvas.height / 2)*0.8,0,Math.PI*2, true); // outer (unfills it)
    ctx.fillStyle = color;
    ctx.fill();

    return true;
}

function updateRing(canvas, value){
    /*Get context and save current color*/
    var ctx = canvas.getContext('2d');
    var color = ctx.fillStyle;
    /*Clear canvas*/
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    /*Draw it again*/
    drawRing(canvas, color, value);
    return true;
}

/***************************************** PAGES *****************************************/

function buildDashboardPage(process, languagePath){

    var lineChart;
    var barChart;
    var table;
    var securityEventCount;
    var qualityEventCount;

    /*Build charts*/
    Chart.defaults.global.defaultFontColor = '#FFFFFF';
    jQuery.ajax({
            url:'/productioncharts',
            type: 'GET',
            data: {'process': process, 'timebase': '01 year'},
            success:  function(response){
                lineChart = new Chart(document.getElementById("lineCanvas"), 
                {
                    type: 'line', 
                    data:   {
                                datasets:   [
                                                {
                                                    data: response['linedata'][0],
                                                    backgroundColor: 'rgba(120, 255, 250, 0.6)',
                                                    label: 'Entrada'
                                                },
                                                {
                                                    data: response['linedata'][1],
                                                    backgroundColor: 'rgba(255, 220, 107, 0.6)',
                                                    label: 'Saída'
                                                },
                                                {
                                                    data: response['linedata'][2],
                                                    backgroundColor: 'rgba(232, 127, 106, 0.6)',
                                                    label: 'Rejeitos'
                                                }
                                            ]
                            }, 
                    options:{   
                                scales:     {   
                                                xAxes:  [
                                                            {   
                                                                type: 'time', 
                                                                distribution: 'series', 
                                                                time:   {
                                                                            displayFormats: {
                                                                                                minute: 'HH:mm', 
                                                                                                hour: 'DD/MM HH:mm', 
                                                                                                day: 'DD/MM HH:mm', 
                                                                                                month:'DD/MM/YY'
                                                                                            }
                                                                        }
                                                            }, 
                                                            {   
                                                                gridLines:  {color:'#FFFFFF'}
                                                            }
                                                        ], 
                                                yAxes: [
                                                            {
                                                                gridLines:  {color:'#FFFFFF'}
                                                            }
                                                        ]
                                            },
                                tooltips:   {   
                                                backgroundColor:'#d5d3bf', 
                                                bodyFontColor:'#000000', 
                                                titleFontColor:'#000000'
                                            },
                                maintainAspectRatio: false,
                                responsive: true,
                                plugins:    {
                                                zoom:   {
                                                            pan:    {
                                                                        enabled: true,
                                                                        mode: 'x',
                                                                    },
                                                            zoom:   {
                                                                        enabled: true,
                                                                        drag: false,
                                                                        mode: 'x'
                                                                    }
                                                        }
                                            }
                            },
                });
                barChart = new Chart(document.getElementById("barCanvas"), 
                {
                    type: 'bar',
                    data:   {
                                labels:     ['Entrada', 'Saída', 'Rejeitos'],
                                datasets:   [
                                                {
                                                    data: response['bardata'],
                                                    backgroundColor:    [
                                                                            'rgba(120, 255, 250, 0.6)', 
                                                                            'rgba(255, 220, 107, 0.6)',
                                                                            'rgba(232, 127, 106, 0.6)'
                                                                        ]        
                                                }
                                            ]
                            },
                    options:    {   
                                    scales:     {
                                                    xAxes:  [   
                                                                {  
                                                                    gridLines:{color:'#FFFFFF'}
                                                                }
                                                            ], 
                                                    yAxes:  [       
                                                                {   
                                                                    gridLines:{color:'#FFFFFF'}, 
                                                                    ticks:{suggestedMax: 100}
                                                                }
                                                            ]
                                                },
                                    tooltips:   {
                                                    backgroundColor:'#d5d3bf', 
                                                    bodyFontColor:'#000000', 
                                                    titleFontColor:'#000000'
                                                },
                                    legend: {display: false},
                                    maintainAspectRatio: false,
                                    responsive: true
                                }
                });
            }
    });

    /*Build local event data table and the rings*/
    jQuery.ajax({
            url:'/events',
            type: 'GET',
            data: {'process': process, 'timebase': '01 year'},
            success:  function(response){
                /*Event table*/
                table = jQuery('#eventtable').DataTable(
                {
                    language:{"url": languagePath},
                    pageLength : 5,
                    bLengthChange: false,
                    bFilter: false,
                    data: response['securityevent'].concat(response['qualityevent']),
                    columns: [{title: "Registro"}, {title: "Data"}, {title: "Origem"}]
                });                       
                /*Event table row handler*/
                jQuery('#eventtable tbody').on('click', 'tr', function () 
                {
                    var tr = jQuery(this).closest('tr');
                    var row = table.row(tr);
                    /*Check if row is empty*/
                    if (typeof row.data() === 'undefined'){return null;}
                    /*Hide or show selected row*/
                    if (jQuery(this).hasClass('tableSelected')){
                        jQuery(this).removeClass('tableSelected');
                        row.child.hide();
                    }
                    else {
                        jQuery(this).addClass('tableSelected');
                        row.child("<p><b>" + row.data()[3] + "</b>: " + row.data()[4] + "</p>").show();
                    }    
                });  
                /*Indicator rings*/
                securityEventCount = response['securityevent'].length;
                qualityEventCount =  response['qualityevent'].length;
                drawRing(document.getElementById("securityCanvas"), "#c08863", securityEventCount);
                drawRing(document.getElementById("qualityCanvas"), "#137478", qualityEventCount);
            }
    });

    /*Timebase button handler*/
    jQuery('#timebasemenu').on('click', 'a', function(e)
    {
        /*Request production info to server*/
        jQuery.ajax({
            url:'/productioncharts',
            type: 'GET',
            data: {'process': process, 'timebase': this.getAttribute('data-time')},
            success:  function(response){
                lineChart.resetZoom();
                lineChart.data.datasets[0].data = response['linedata'][0];
                lineChart.data.datasets[1].data = response['linedata'][1];
                lineChart.data.datasets[2].data = response['linedata'][2];
                barChart.data.datasets[0].data = response['bardata'];
                lineChart.update();
                barChart.update();
            }
        });

        /*Request events info to server*/
        jQuery.ajax({
            url:'/events',
            type: 'GET',
            data: {'process': process, 'timebase': this.getAttribute('data-time')},
            success:  function(response){
                /*Update events datatable*/
                table.clear();
                console.log(response);
                console.log(Array.isArray(response));
                table.rows.add(response['securityevent'].concat(response['qualityevent']));
                table.draw();
                /*Update rings*/
                securityEventCount = response['securityevent'].length;
                qualityEventCount =  response['qualityevent'].length;
                updateRing(document.getElementById("securityCanvas"), securityEventCount);
                updateRing(document.getElementById("qualityCanvas"), qualityEventCount);
            }
        });

    });

    /*Download report*/
    jQuery('#report').on('click', function(e)
    {
        /*Get current time*/
        var current_date = new Date();
        /*Build pdf doc*/
        const doc = new jspdf.jsPDF("p", "mm", "a4");
        doc.setFontSize(20);
        doc.text("Relatório - " + this.getAttribute('data-name'), 10, 20);
        doc.line(10, 30, 200, 30);
        doc.setFontSize(10);
        doc.text("Data da análise: " + current_date.toLocaleString(), 10, 40);
        doc.text("Quantidade de ocorrências de Segurança: " + String(securityEventCount), 10, 50);
        doc.text("Quantidade de ocorrências de Qualidade: " + String(qualityEventCount), 10, 60);
        doc.line(10, 70, 200, 70);
        doc.addImage(document.getElementById("lineCanvas").toDataURL("image/jpeg"), 'JPEG', 10, 80, 190, 80);
        doc.addImage(document.getElementById("barCanvas").toDataURL("image/jpeg"), 'JPEG', 10, 170, 190, 80);
        /*Save and download it*/
        doc.save("relatorio " + current_date.toLocaleString() + ".pdf"); 
            
    });
}

function buildEventsPage(languagePath){
    
    var table;

    /*Build total event data table*/
    jQuery.ajax({
            url:'/events',
            type: 'GET',
            data: {'process': 'all', 'timebase': '01 year'},
            success:  function(response){
                /*Event table*/
                table = jQuery('#eventtable').DataTable(
                {
                    language:{"url": languagePath},
                    pageLength : 5,
                    bLengthChange: false,
                    bFilter: true,
                    data: response['all'],
                    bAutoWidth: false,
                    columns: [{title: "Registro"}, {title: "Data"}, {title: "Origem"}, {title: "Usuário"}, {title: "Descrição"}, {title: "Processo"}]
                });

                /*Event table row handler*/
                jQuery('#eventtable tbody').on('click', 'tr', function () 
                {
                    var tr = jQuery(this).closest('tr');
                    var row = table.row(tr);
                    /*Check if row is empty*/
                    if (typeof row.data() === 'undefined'){return null;}
                    /*Selected row*/
                    if (jQuery(this).hasClass('tableSelected')){
                        jQuery(this).removeClass('tableSelected');
                    }
                    else {
                        table.$('tr.tableSelected').removeClass('tableSelected');
                        jQuery(this).addClass('tableSelected');
                    }        
                });
            }
    });
    
    /*New event*/
    jQuery('#addButton').on('click', function(e){
        jQuery('#eventsAddModal').modal('show');
    });
    jQuery('#eventsAddForm').on('submit', function(e){
        jQuery.ajax({
            url: '/events',
            type: 'POST',
            data: {'process': jQuery('#addEventsProcess').val(), 'source': jQuery('#addEventsSource').val(), 'description': jQuery('#addEventsDescription').val()}, 
            success: function(response){
                jQuery('#eventsAddForm').modal('hide');
                jQuery('#message').modal('show');
                jQuery('#messageText').text('Evento adicionado com sucesso');
                setTimeout(function(){ 
                    jQuery('#message').modal('hide'); 
                }, 1500);  
            }
        });

    });

    /*Edit event*/
    jQuery('#editButton').on('click', function(e){
        var selectedRow = table.row('.tableSelected');
        if(selectedRow[0].length == 0){
            jQuery('#message').modal('show');
            jQuery('#messageText').text('Ocorrência não selecionada');
            setTimeout(function(){ 
                jQuery('#message').modal('hide'); 
            }, 1500);  
            return null;
        };
        /*Restore selected user data*/
        jQuery('#editEventsID').val(selectedRow.data()[0]);
        jQuery('#editEventsProcess').val(selectedRow.data()[5]);
        jQuery('#editEventsSource').val(selectedRow.data()[2]);
        jQuery('#editEventsDescription').val(selectedRow.data()[4]);
        /*Show edit user modal*/
        jQuery('#eventsEditModal').modal('show');
    });
    jQuery('#eventsEditForm').on('submit', function(e){
        jQuery('#eventsEditModal').modal('hide');
        jQuery.ajax({
            url: '/events',
            type: 'PUT',
            data: {'eventid': jQuery('#editEventsID').val(), 'process': jQuery('#editEventsProcess').val(), 'source': jQuery('#editEventsSource').val(), 'description': jQuery('#editEventsDescription').val()}, 
            success: function(response){
                jQuery('#message').modal('show');
                jQuery('#messageText').text('Evento modificado com sucesso');
                setTimeout(function(){ 
                    jQuery('#message').modal('hide'); 
                }, 1500);  
            } 
        });

    });

    /*Delete event*/ 
    jQuery('#deleteButton').on('click', function(e){
        var selectedRow = table.row('.tableSelected');
        if(selectedRow[0].length == 0){
            jQuery('#message').modal('show');
            jQuery('#messageText').text('Ocorrência não selecionada');
            setTimeout(function(){ 
                jQuery('#message').modal('hide'); 
            }, 1500);  
            return null;
        };
        jQuery('#deleteMessage').modal('show');
    });
    jQuery('#deleteConfirmation').on('click', function(e){
        jQuery('#deleteMessage').modal('hide');
        var selectedRow = table.row('.tableSelected');
        jQuery.ajax({
            url: '/events',
            type: 'DELETE',
            data: {'eventid': selectedRow.data()[0]},
            success: function(response){
                jQuery('#message').modal('show');
                jQuery('#messageText').text('Evento removido com sucesso');
                setTimeout(function(){ 
                    jQuery('#message').modal('hide'); 
                }, 1500);  
                selectedRow.remove().draw();
            }
        });
    });

    /*Update events table*/
    jQuery('#timebasemenu').on('click', 'a', function(e){
        /*Request events info to server*/
        jQuery.ajax({
            url:'/events',
            type: 'GET',
            data: {'process': 'all', 'timebase': this.getAttribute('data-time')},
            success:  function(response){
                /*Update events datatable*/
                table.clear();
                console.log(response);
                console.log(Array.isArray(response));
                table.rows.add(response['all']);
                table.draw();
            }
        });

    });

}

function buildUsersPage(languagePath){
    var table;

    /*Build users data table*/
    jQuery.ajax({
        url:'/users',
        type: 'GET',
        data: {},
        success:  function(response){
            /*Users table*/
            table = jQuery('#userstable').DataTable(
            {
                language:{"url": languagePath},
                pageLength : 10,
                bLengthChange: false,
                bFilter: true,
                data: response['users'],
                columns: [{title: "N° registro"}, {title: "Usuário"}, {title: "Nome"}, {title: "Setor"}, {title: "Nível Acesso"}]
            });
            /*Users table row handler*/
            jQuery('#userstable tbody').on('click', 'tr', function () 
            {
                var tr = jQuery(this).closest('tr');
                var row = table.row(tr);
                /*Check if row is empty*/
                if (typeof row.data() === 'undefined'){return null;}
                /*Selected row*/
                if (jQuery(this).hasClass('tableSelected')){
                    jQuery(this).removeClass('tableSelected');
                }
                else {
                    table.$('tr.tableSelected').removeClass('tableSelected');
                    jQuery(this).addClass('tableSelected');
                }    

            });
        }
    });

    /*New user*/
    jQuery('#addButton').on('click', function(e){
        jQuery('#userAddModal').modal('show');
    });
    jQuery('#addUserLogin').on('blur', function(e){
        jQuery.ajax({
            url: '/isuseravailable',
            type: 'GET',
            data: {'userlogin': jQuery('#addUserLogin').val()}, 
            success: function(response){
                if (response['available']){
                    jQuery('#addUserLoginError').text('');
                }
                else{
                    jQuery('#addUserLoginError').text('Usuário já existente');
                    jQuery('#addUserLogin').val('');
                }
            }
        });

    });
    jQuery('#userAddForm').on('submit', function(e){
        jQuery.ajax({
            url: '/users',
            type: 'POST',
            data: {'userlogin': jQuery('#addUserLogin').val(), 'username': jQuery('#AddUserName').val(), 'usersector': jQuery('#AddUserSector').val(), 'userprivileges': jQuery('#AddUserPrivileges').val()}, 
            success: function(response){
                jQuery('#userAddModal').modal('hide');
                jQuery('#message').modal('show');
                jQuery('#messageText').text('Usuário adicionado com sucesso');
                setTimeout(function(){ 
                    jQuery('#message').modal('hide');
                    location.reload();  
                }, 1500);  
            }
        });

    });

    

    /*Delete user*/ 
    jQuery('#deleteButton').on('click', function(e){
        var selectedRow = table.row('.tableSelected');
        if(selectedRow[0].length == 0){
            jQuery('#message').modal('show');
            jQuery('#messageText').text('Usuário não selecionado');
            setTimeout(function(){ 
                jQuery('#message').modal('hide'); 
            }, 1500);  
            return null;
        };
        jQuery('#deleteMessage').modal('show');
    });
    jQuery('#deleteConfirmation').on('click', function(e){
        jQuery('#deleteMessage').modal('hide');
        var selectedRow = table.row('.tableSelected');
        jQuery.ajax({
            url: '/users',
            type: 'DELETE',
            data: {'userid': selectedRow.data()[0]},
            success: function(response){
                jQuery('#message').modal('show');
                jQuery('#messageText').text('Usuário removido com sucesso');
                setTimeout(function(){ 
                    jQuery('#message').modal('hide'); 
                }, 1500);  
                selectedRow.remove().draw();
            }
        });
    });
    
}

function buildLogin(){

        /*Logout request*/
        jQuery('#logoutButton').on('click', function(e){
            jQuery.ajax({
                url: '/logout',
                type: 'GET',
                data: {}, 
                success: function(response){
                    jQuery('#message').modal('show');
                    jQuery('#messageText').text('Logout efetuado com sucesso');
                    setTimeout(function(){ 
                        jQuery('#message').modal('hide'); 
                        location.reload();  
                    }, 1500);
                } 
            });
        });

        /*Change password request*/
        jQuery('#changePasswordButton').on('click', function(e){
            jQuery('#changePasswordModal').modal('show');
        });
        jQuery('#confirmPassword').on('blur', function(e){
            if (jQuery('#newPassword').val() != jQuery('#confirmPassword').val()){
                jQuery('#confirmPassword').val('');
                jQuery('#changePasswordError').text('As senhas não conferem');
            }
            else{
                jQuery('#changePasswordError').text('');
            }
        });
        jQuery('#changePasswordForm').on('submit', function(e){
            e.preventDefault();
            jQuery.ajax({
                url: '/changeuserpassword',
                type: 'PUT',
                data: {'currentPassword': jQuery('#currentPassword').val(), 'newPassword': jQuery('#newPassword').val()}, 
                success: function(response){
                    jQuery('#changePasswordModal').modal('hide');
                    if(response['changeUserPassword']){
                        jQuery('#message').modal('show');
                        jQuery('#messageText').text('A senha foi alterada com sucesso');
                        setTimeout(function(){ 
                            jQuery('#message').modal('hide'); 
                        }, 1500);  
                    }
                    else{
                        jQuery('#message').modal('show');
                        jQuery('#messageText').text('Não foi possível realizar a alteração: senha atual incorreta');  
                        setTimeout(function(){ 
                            jQuery('#message').modal('hide'); 
                        }, 1500);                        
                    }
                }
            });
        });
}
