function varargout = main_menu_window(varargin)

% Begin initialization code - DO NOT EDIT
gui_Singleton = 0;
gui_State = struct('gui_Name',       mfilename, ...
                   'gui_Singleton',  gui_Singleton, ...
                   'gui_OpeningFcn', @main_menu_window_OpeningFcn, ...
                   'gui_OutputFcn',  @main_menu_window_OutputFcn, ...
                   'gui_LayoutFcn',  [] , ...
                   'gui_Callback',   []);
if nargin && ischar(varargin{1})
    gui_State.gui_Callback = str2func(varargin{1});
end

if nargout
    [varargout{1:nargout}] = gui_mainfcn(gui_State, varargin{:});
else
    gui_mainfcn(gui_State, varargin{:});
end
% End initialization code - DO NOT EDIT

%-------------------------------------------------------------------------
%   Main menu opening function 
%-------------------------------------------------------------------------
function main_menu_window_OpeningFcn(hObject, eventdata, handles, varargin)
% global SCRS SCRW_X SCRW_Y % screen size (1x4, [x y width height]) & width
% Choose default command line output for main_menu_window
global SCRS SCRW_X SCRW_Y % screen size (1x4, [x y width height]) & width

handles.output = hObject;
% Update handles structure
guidata(hObject, handles);

    h = findobj('Tag','main_menu_window');
    j = get(h,'Position');
    wind_width = j(1,3);
    wind_height = j(1,4);
    xpos = SCRW_X;
    ypos = (SCRS(1,4) - SCRW_Y) - wind_height;
    set(hObject,'Position',[xpos ypos wind_width wind_height]);

%-------------------------------------------------------------------------
%   Main menu closing function 
%-------------------------------------------------------------------------
function varargout = main_menu_window_OutputFcn(hObject, eventdata, handles) 
% Get default command line output from handles structure
varargout{1} = handles.output;

%=========================================================================
%    DATA (menu)
%=========================================================================
function data_menu_Callback(hObject, eventdata, handles)

%-------------------------------------------------------------------------
%           ABOUT (submenu)  
%-------------------------------------------------------------------------
function menu_about_Callback(hObject, eventdata, handles)
global CURRENT_VERSION
cd slides
str = ['About_image.jpg'];
[x,imap] = imread(str);
if exist('x')==1
    h = figure('Menubar','none','NumberTitle','off');
    axes('position',[0 0 1 1]);
    axis image;
    image(x)
    drawnow
    %===== version check ===========================
    try
%         temp  = urlread('http://www.coulombstress.org/version/version.txt');
        temp  = '3.2.01'; % temporal for Sep. 12 2010 SCEC class
        idx   = strfind(temp,'.');
        newvs = str2num([temp(1:idx(1)-1) temp(idx(1)+1:idx(2)-1) temp(idx(2)+1:end)]);
        idx   = strfind(CURRENT_VERSION,'.');
        curvs = str2num([CURRENT_VERSION(1:idx(1)-1) CURRENT_VERSION(idx(1)+1:idx(2)-1) CURRENT_VERSION(idx(2)+1:end)]);
        if newvs > curvs
            versionmsg = [' New version ' temp ' is found. Visit the following website.'];
        else
            versionmsg = '';
        end
    catch
        % in case user cannot access our site
            versionmsg = 'No internet connection. Check the version later.';
    end
    
    th = text(460.0,385.0,['  version ' CURRENT_VERSION '  ']);
    set(th,'fontsize',16,'fontweight','b','Color','w',...
        'horizontalalignment','center','verticalalignment','middle',...
        'backgroundcolor','none','edgecolor','none')
    th1 = text(305.0,420.0,versionmsg);
    set(th1,'fontsize',14,'fontweight','b','Color','w',...
        'horizontalalignment','center','verticalalignment','middle',...
        'backgroundcolor','k','edgecolor','none')
    th2 = text(320.0,420.0,' http://earthquake.usgs.gov/research/modeling/coulomb/ ');
    set(th2,'fontsize',12,'fontweight','b','Color','w',...
        'horizontalalignment','center','verticalalignment','middle',...
        'backgroundcolor','none','edgecolor','none')

% http://earthquake.usgs.gov/research/modeling/coulomb/
%     new_version =
%     urlread('http://www.coulombstress.org/version/version.txt');
    
end
cd ..

%-------------------------------------------------------------------------
%           NEW (submenu)  
%-------------------------------------------------------------------------
function menu_new_Callback(hObject, eventdata, handles)
global GRID FUNC_SWITCH ICOORD
global H_GRID_INPUT COAST_DATA AFAULT_DATA
global ELEMENT IACT S_ELEMENT INPUT_FILE INUM
coulomb_init;
clear_obj_and_subfig;
IACT = 0;
INUM = 0;
ELEMENT = []; S_ELEMENT = [];
GRID = [];
COAST_DATA = []; AFAULT_DATA = [];
INPUT_FILE = 'untitled';
if ICOORD == 2          % in case the current coordinates mode is 'Lon & lat' (ICOORD=2)
    h = warndlg('Coordinates mode automatically changes to ''Cartesian'' now','!! Warning !!');
    waitfor(h);
    ICOORD = 1;         % change to x & y cartesian coordinates
end
if isempty(GRID)
    % default values
    GRID(1,1) = -50.01; % x start
    GRID(2,1) = -50.01; % y start
    GRID(3,1) =  50.00; % x finish
    GRID(4,1) =  50.00; % y finish
    GRID(5,1) =   5.00; % x increment
    GRID(6,1) =   5.00; % y increment
end
H_GRID_INPUT = grid_input_window;
FUNC_SWITCH = 0;
if ~isempty(GRID)
    all_functions_enable_on;
    set(findobj('Tag','menu_file_save'),'Enable','On');
    set(findobj('Tag','menu_file_save_ascii'),'Enable','On');
    set(findobj('Tag','menu_file_save_ascii2'),'Enable','On');
    set(findobj('Tag','menu_map_info'),'Enable','On');
    all_overlay_enable_off;
    set(findobj('Tag','menu_trace_put_faults'),'Enable','On'); 
end

%-------------------------------------------------------------------------
%           NEW from Map (submenu)  
%-------------------------------------------------------------------------
function menu_new_map_Callback(hObject, eventdata, handles)
global H_UTM GRID COAST_DATA AFAULT_DATA
global IACT INPUT_FILE INUM
coulomb_init;
clear_obj_and_subfig;
IACT = 0;
INUM = 0;
COAST_DATA = []; AFAULT_DATA = [];
INPUT_FILE = 'untitled';
% all off
set(findobj('Tag','menu_file_save'),'Enable','Off');
set(findobj('Tag','menu_file_save_ascii'),'Enable','Off');
set(findobj('Tag','menu_file_save_ascii2'),'Enable','Off');
all_functions_enable_off;
all_overlay_enable_off;
%
H_UTM = utm_window;
waitfor(H_UTM);
if ~isempty(GRID)
    all_functions_enable_on;
    set(findobj('Tag','menu_file_save'),'Enable','On');
    set(findobj('Tag','menu_file_save_ascii'),'Enable','On');
    set(findobj('Tag','menu_file_save_ascii2'),'Enable','On');
    set(findobj('Tag','menu_map_info'),'Enable','On');
    all_overlay_enable_on;
    set(findobj('Tag','menu_focal_mech'),'Enable','On');
end

%-------------------------------------------------------------------------
%           OPEN/most recent file (submenu)  
%-------------------------------------------------------------------------
function menu_most_recent_file_Callback(hObject, eventdata, handles)
global GRID
global FUNC_SWITCH DIALOG_SKIP
global COAST_DATA AFAULT_DATA EQ_DATA GPS_DATA
global VOLCANO
coulomb_init;
clear_obj_and_subfig;
DIALOG_SKIP = 0;
last_input;
FUNC_SWITCH = 0;
if ~isempty(GRID)
    all_functions_enable_on;
    set(findobj('Tag','menu_file_save'),'Enable','On');
    set(findobj('Tag','menu_file_save_ascii'),'Enable','On');
    set(findobj('Tag','menu_file_save_ascii2'),'Enable','On');
    set(findobj('Tag','menu_map_info'),'Enable','On');
    all_overlay_enable_off;
    set(findobj('Tag','menu_trace_put_faults'),'Enable','On'); 
end
if isempty(EQ_DATA)
    set(findobj('Tag','menu_focal_mech'),'Enable','Off');
else
    set(findobj('Tag','menu_focal_mech'),'Enable','On');
end
% ---- making grid map view -----------------------------
% put try-catch-end in case user push "cancel button"
% try
%     check_overlay_items;
%     menu_grid_mapview_Callback;
% catch
%     return
% end

%-------------------------------------------------------------------------
%           OPEN (submenu)  
%-------------------------------------------------------------------------
function menu_file_open_Callback(hObject, eventdata, handles)
global GRID
global H_MAIN FUNC_SWITCH EQ_DATA DIALOG_SKIP
% coulomb_init;
% clear_obj_and_subfig;
DIALOG_SKIP = 0;
input_open(1);

% FUNC_SWITCH = 0;
if ~isempty(GRID)
    all_functions_enable_on;
    set(findobj('Tag','menu_file_save'),'Enable','On');
    set(findobj('Tag','menu_file_save_ascii'),'Enable','On');
    set(findobj('Tag','menu_file_save_ascii2'),'Enable','On');
    set(findobj('Tag','menu_map_info'),'Enable','On');
    all_overlay_enable_off;
    set(findobj('Tag','menu_trace_put_faults'),'Enable','On'); 
end
% menu_clear_overlay_Callback;
check_overlay_items;

%-------------------------------------------------------------------------
%           OPEN/SKIPPING DIALOG (submenu)  
%-------------------------------------------------------------------------
function menu_open_skipping_Callback(hObject, eventdata, handles)
global GRID FUNC_SWITCH
global DIALOG_SKIP IACT
% coulomb_init;
% clear_obj_and_subfig;
DIALOG_SKIP = 0;
input_open(3);          % 3 means skipping the open window

% FUNC_SWITCH = 0;
if ~isempty(GRID)
    all_functions_enable_on;
    set(findobj('Tag','menu_file_save'),'Enable','On');
    set(findobj('Tag','menu_file_save_ascii'),'Enable','On');
    set(findobj('Tag','menu_file_save_ascii2'),'Enable','On');
    set(findobj('Tag','menu_map_info'),'Enable','On');
    all_overlay_enable_off;
    set(findobj('Tag','menu_trace_put_faults'),'Enable','On'); 
end
try
    check_overlay_items;
    if IACT == 0 % if user select cancel, IACT is 1 forwarded from 'input_open.m'
    menu_grid_mapview_Callback;
    FUNC_SWITCH = 0;
    end
catch
    return
end

%-------------------------------------------------------------------------
%           SAVE  AS .MAT(submenu)  
%-------------------------------------------------------------------------
function menu_file_save_Callback(hObject, eventdata, handles)
global INUM HEAD NUM POIS CALC_DEPTH YOUNG FRIC R_STRESS ID KODE ELEMENT
global FCOMMENT GRID SIZE SECTION
global MIN_LAT MAX_LAT ZERO_LAT MIN_LON MAX_LON ZERO_LON
global PREF
global COAST_DATA AFAULT_DATA EQ_DATA GPS_DATA
global VOLCANO SEISSTATION
global HOME_DIR PREF_DIR
    if isempty(PREF)==1
       % make default values & then save them.
       PREF = [1.0 0.0 0.0 1.2;...
               0.0 0.0 0.0 1.0;...
               0.7 0.7 0.0 0.2;...
               0.0 0.0 0.0 1.2;...
               1.0 0.5 0.0 3.0;...
               0.2 0.2 0.2 1.0;...
               2.0 0.0 0.0 0.0;...
               1.0 0.0 0.0 0.0;...
               0.9 0.9 0.1 1.0];    % volcano
    end
    if isempty(PREF_DIR) ~= 1
        try
            cd(PREF_DIR);
        catch
            cd(HOME_DIR);
        end
    else
        try
            cd('input_files');
        catch
            cd(HOME_DIR);
        end    
    end
    [filename,pathname] = uiputfile('*.mat',...
        ' Save Input File As');
    if isequal(filename,0) | isequal(pathname,0)
        disp('User selected Cancel')
    else
        disp(['User saved as ', fullfile(pathname,filename)])
    end
    save(fullfile(pathname,filename), 'HEAD','NUM','POIS','CALC_DEPTH',...
        'YOUNG','FRIC','R_STRESS','ID','KODE','ELEMENT','FCOMMENT',...
        'GRID','SIZE','SECTION','PREF','MIN_LAT','MAX_LAT','ZERO_LAT',...
        'MIN_LON','MAX_LON','ZERO_LON','COAST_DATA','AFAULT_DATA',...
        'EQ_DATA','GPS_DATA','VOLCANO','SEISSTATION',...
        '-mat');
    cd(HOME_DIR);
    
%-------------------------------------------------------------------------
%           SAVE AS ASCII (submenu)  
%-------------------------------------------------------------------------
function menu_file_save_ascii_Callback(hObject, eventdata, handles)
global PREF HOME_DIR PREF_DIR IRAKE
    IRAKE = 0;
    if isempty(PREF)==1
       % make default values & then save them.
       PREF = [1.0 0.0 0.0 1.2;...
               0.0 0.0 0.0 1.0;...
               0.7 0.7 0.0 0.2;...
               0.0 0.0 0.0 1.2;...
               1.0 0.5 0.0 3.0;...
               0.2 0.2 0.2 1.0;...
               2.0 0.0 0.0 0.0;...
               1.0 0.0 0.0 0.0];
    end
    if isempty(PREF_DIR) ~= 1
        try
            cd(PREF_DIR);
        catch
            cd(HOME_DIR);
        end
    else
        try
            cd('input_files');
        catch
            cd(HOME_DIR);
        end    
    end
    [filename,pathname] = uiputfile('*.inp',...
        ' Save Input File As');
    if isequal(filename,0) | isequal(pathname,0)
        disp('User selected Cancel')
    else
        disp(['User saved as ', fullfile(pathname,filename)])
    end
    cd(pathname);
    input_save_ascii;
    cd(HOME_DIR);
     
%-------------------------------------------------------------------------
%           SAVE AS ASCII2 (submenu)  - save as "rake" & "net slip"
%-------------------------------------------------------------------------
function menu_file_save_ascii2_Callback(hObject, eventdata, handles)
global PREF HOME_DIR PREF_DIR IRAKE
    IRAKE = 1;
    if isempty(PREF)==1
       % make default values & then save them.
       PREF = [1.0 0.0 0.0 1.2;...
               0.0 0.0 0.0 1.0;...
               0.7 0.7 0.0 0.2;...
               0.0 0.0 0.0 1.2;...
               1.0 0.5 0.0 3.0;...
               0.2 0.2 0.2 1.0;...
               2.0 0.0 0.0 0.0;...
               1.0 0.0 0.0 0.0];
    end
    if isempty(PREF_DIR) ~= 1
        try
            cd(PREF_DIR);
        catch
            cd(HOME_DIR);
        end
    else
        try
            cd('input_files');
        catch
            cd(HOME_DIR);
        end    
    end
    [filename,pathname] = uiputfile('*.inr',...
        ' Save Input File As');
    if isequal(filename,0) | isequal(pathname,0)
        disp('User selected Cancel')
        cd(HOME_DIR); return
    else
        disp(['User saved as ', fullfile(pathname,filename)])
        cd(pathname);
        input_save_ascii;
        cd(HOME_DIR);
    end


%-------------------------------------------------------------------------
%           PUT MAP INFO (submenu)  
%-------------------------------------------------------------------------
function menu_map_info_Callback(hObject, eventdata, handles)
global H_STUDY_AREA H_MAIN
H_STUDY_AREA = study_area;
waitfor(H_STUDY_AREA);      % wait for user's input of lat & lon info.
h = findobj('Tag','main_menu_window');
if isempty(h)~=1 & isempty(H_MAIN)~=1 
    iflag = check_lonlat_info;
    if iflag == 1
    all_overlay_enable_on;
%    set(findobj('Tag','menu_focal_mech'),'Enable','On');
    end
end

%-------------------------------------------------------------------------
%           PREFERENCES (submenu)  
%-------------------------------------------------------------------------
function menu_preferences_Callback(hObject, eventdata, handles)
global OUTFLAG
preference_window;
if OUTFLAG == 1
    h = findobj('Tag','Radiobutton_output');
    set(h,'Value',1);
    h = findobj('Tag','Radiobutton_input');
    set(h,'Value',0);
else
    h = findobj('Tag','Radiobutton_output');
    set(h,'Value',0);
    h = findobj('Tag','Radiobutton_input');
    set(h,'Value',1);
end

%-------------------------------------------------------------------------
%           QUIT (submenu)  
%-------------------------------------------------------------------------
function menu_quit_Callback(hObject, eventdata, handles)
global PREF OUTFLAG PREF_DIR HOME_DIR H_HELP INPUT_FILE FNUM_ONOFF
subfig_clear;
tempdir = pwd;
if ~strcmp(tempdir,HOME_DIR)
    cd(HOME_DIR);
end
cd preferences
    dlmwrite('preferences.dat',PREF,'delimiter',' ','precision','%3.1f');
            if isempty(OUTFLAG) == 1
                OUTFLAG = 1;
            end
            if isempty(PREF_DIR) == 1
                PREF_DIR = HOME_DIR;
            end
            if isempty(INPUT_FILE) == 1
                INPUT_FILE = 'empty';
            end
    save preferences2.mat PREF_DIR INPUT_FILE OUTFLAG FNUM_ONOFF;
cd ..
h = figure(gcf);
delete(h);
% for help window (H_HELP)
h = findobj('Tag','coulomb_help_window');
if (isempty(h)~=1 && isempty(H_HELP)~=1)
    close(figure(H_HELP))
    H_HELP = [];
end

%=========================================================================
%    FUNCTIONS (menu)
%=========================================================================
function function_menu_Callback(hObject, eventdata, handles)

%-------------------------------------------------------------------------
%           GRID (submenu)  
%-------------------------------------------------------------------------
function menu_grid_Callback(hObject, eventdata, handles)

% --------------------------------------------------------------------
function menu_grid_mapview_Callback(hObject, eventdata, handles)
global FUNC_SWITCH ICOORD LON_GRID COAST_DATA EQ_DATA GPS_DATA AFAULT_DATA
global ELEMENT ID KODE
% global H_MAIN
subfig_clear;
FUNC_SWITCH = 1;
grid_drawing;
fault_overlay;
%if ICOORD == 2 && isempty(LON_GRID) ~= 1
    if isempty(COAST_DATA)~=1 | isempty(EQ_DATA)~=1 |...
            isempty(AFAULT_DATA)~=1 | isempty(GPS_DATA)~=1
        hold on;
        overlay_drawing;
    end
%end
FUNC_SWITCH = 0; %reset
flag = check_lonlat_info;
if flag == 1
    all_overlay_enable_on;
%    set(findobj('Tag','menu_focal_mech'),'Enable','On');  
end

% --------------------------------------------------------------------
function menu_grid_3d_Callback(hObject, eventdata, handles)
global FUNC_SWITCH F3D_SLIP_TYPE H_F3D_VIEW
global ELEMENT POIS YOUNG FRIC ID H_MAIN H_VIEWPOINT
global ICOORD LON_GRID
global C_SLIP_SAT
% % so far we cannot use "annotations" in 3D plot
if ICOORD == 2 && isempty(LON_GRID) ~= 1
    h = warndlg('Sorry this is not available for lat/lon coordinates. Change to Cartesian coordinates.',...
        '!! Warning !!');
    waitfor(h);
    return
end
subfig_clear;
hc = wait_calc_window;
FUNC_SWITCH = 1;
F3D_SLIP_TYPE = 1;  % net slip
element_condition(ELEMENT,POIS,YOUNG,FRIC,ID);

C_SLIP_SAT = [];
grid_drawing_3d;
displ_open(2);

H_F3D_VIEW = f3d_view_control_window;
% figure(H_MAIN);
% menu_gps_Callback;
gps_3d_overlay;

flag = check_lonlat_info;
if flag == 1
    all_overlay_enable_on;
end
close(hc);

%-------------------------------------------------------------------------
%           DISPLACEMENT (submenu)  with sub-submenu
%-------------------------------------------------------------------------
function menu_displacement_Callback(hObject, eventdata, handles)

%-------------------------------------------------------------------------
%                       VECTORS (sub-submenu)
%-------------------------------------------------------------------------
function menu_vectors_Callback(hObject, eventdata, handles)
global FUNC_SWITCH
global DC3D IACT
global H_DISPL ICOORD FIXFLAG INPUT_FILE
global COAST_DATA EQ_DATA AFAULT_DATA GPS_DATA
global GPS_FLAG GPS_SEQN_FLAG
global OUTFLAG PREF_DIR HOME_DIR H_MAIN
subfig_clear;
FUNC_SWITCH = 2;
FIXFLAG = 0;
% to escape recalculation of Okada half space
if IACT ~= 1        
Okada_halfspace;
end
IACT = 1;           % to keep okada output
    a = DC3D(:,1:2);
    b = DC3D(:,5:8);
    c = horzcat(a,b);
    format long;
    if OUTFLAG == 1 | isempty(OUTFLAG) == 1
	cd output_files;
    else
	cd (PREF_DIR);
    end
    header1 = ['Input file selected: ',INPUT_FILE];
    header2 = 'x y z UX UY UZ';
    header3 = '(km) (km) (km) (m) (m) (m)';
    dlmwrite('Displacement.cou',header1,'delimiter',''); 
    dlmwrite('Displacement.cou',header2,'-append','delimiter',''); 
    dlmwrite('Displacement.cou',header3,'-append','delimiter',''); 
    dlmwrite('Displacement.cou',c,'-append','delimiter','\t','precision','%.8f');
    disp(['Displacement.cou is saved in ' pwd]);
    cd (HOME_DIR);
displ_open(2);
H_DISPL = displ_h_window;
if ICOORD == 1
    set(findobj('Tag','radiobutton_fixlonlat'),'Visible','off');
    set(findobj('Tag','text_disp_lon'),'Visible','off');
    set(findobj('Tag','text_disp_lat'),'Visible','off');
    set(findobj('Tag','edit_fixlon'),'Visible','off');
    set(findobj('Tag','edit_fixlat'),'Visible','off');
else
    set(findobj('Tag','radiobutton_fixcart'),'Visible','off');
    set(findobj('Tag','text_cart_x'),'Visible','off');
    set(findobj('Tag','text_cart_y'),'Visible','off');
    set(findobj('Tag','text_x_km'),'Visible','off');
    set(findobj('Tag','text_y_km'),'Visible','off');
    set(findobj('Tag','edit_fixx'),'Visible','off');
    set(findobj('Tag','edit_fixy'),'Visible','off');    
end
flag = check_lonlat_info;
if flag == 1
    all_overlay_enable_on;
%	set(findobj('Tag','menu_focal_mech'),'Enable','On');
end
% ----- overlay drawing --------------------------------
%if ICOORD == 2 && isempty(LON_GRID) ~= 1
    if isempty(COAST_DATA)~=1 | isempty(EQ_DATA)~=1 |...
            isempty(AFAULT_DATA)~=1 | isempty(GPS_DATA)~=1
        figure(H_MAIN); hold on;
        overlay_drawing;
end

%-------------------------------------------------------------------------
%                       WIREFRAME (sub-submenu)
%-------------------------------------------------------------------------
function menu_wireframe_Callback(hObject, eventdata, handles)
global FUNC_SWITCH FIXFLAG
global DC3D IACT
global H_DISPL ICOORD INPUT_FILE
global COAST_DATA EQ_DATA AFAULT_DATA GPS_DATA
global OUTFLAG PREF_DIR HOME_DIR H_MAIN
subfig_clear;
FUNC_SWITCH = 3;
FIXFLAG    = 0;
% to escape recalculation of Okada half space
if IACT ~= 1        
Okada_halfspace;
end
IACT = 1;           % to keep okada output
    a = DC3D(:,1:2);
    b = DC3D(:,5:8);
    c = horzcat(a,b);
    format long;
    if OUTFLAG == 1 | isempty(OUTFLAG) == 1
	cd output_files;
    else
	cd (PREF_DIR);
    end
    % save Displacement.cou a -ascii
    header1 = ['Input file selected: ',INPUT_FILE];
    header2 = 'x y z UX UY UZ';
    header3 = '(km) (km) (km) (m) (m) (m)';
    dlmwrite('Displacement.cou',header1,'delimiter',''); 
    dlmwrite('Displacement.cou',header2,'-append','delimiter','\t'); 
    dlmwrite('Displacement.cou',header3,'-append','delimiter','\t'); 
    dlmwrite('Displacement.cou',c,'-append','delimiter','\t','precision','%.8f');
    disp(['Displacement.cou is saved in ' pwd]);
    cd (HOME_DIR);  
displ_open(2);
H_DISPL = displ_h_window;
    set(findobj('Tag','radiobutton_fixlonlat'),'Visible','off');
    set(findobj('Tag','radiobutton_fixcart'),'Visible','off');
    set(findobj('Tag','text_cart_x'),'Visible','off');
    set(findobj('Tag','text_cart_y'),'Visible','off');
    set(findobj('Tag','edit_fixx'),'Visible','off');
    set(findobj('Tag','edit_fixy'),'Visible','off');
    set(findobj('Tag','text_x_km'),'Visible','off');
    set(findobj('Tag','text_y_km'),'Visible','off');
    set(findobj('Tag','text_disp_lon'),'Visible','off');
    set(findobj('Tag','text_disp_lat'),'Visible','off');
    set(findobj('Tag','edit_fixlon'),'Visible','off');
    set(findobj('Tag','edit_fixlat'),'Visible','off');
    set(findobj('Tag','Mouse_click'),'Visible','off');
flag = check_lonlat_info;
if flag == 1
    all_overlay_enable_on;
%    set(findobj('Tag','menu_focal_mech'),'Enable','On');
end
% ----- overlay drawing --------------------------------
%if ICOORD == 2 && isempty(LON_GRID) ~= 1
    if isempty(COAST_DATA)~=1 | isempty(EQ_DATA)~=1 |...
            isempty(AFAULT_DATA)~=1 | isempty(GPS_DATA)~=1
        figure(H_MAIN); hold on;
        overlay_drawing;
end

%-------------------------------------------------------------------------
%                       CONTOURS (sub-submenu)
%-------------------------------------------------------------------------
function menu_contours_Callback(hObject, eventdata, handles)
global FUNC_SWITCH
global DC3D IACT VD_CHECKED SHADE_TYPE INPUT_FILE
global COAST_DATA EQ_DATA AFAULT_DATA GPS_DATA
global OUTFLAG PREF_DIR HOME_DIR H_MAIN
subfig_clear;
FUNC_SWITCH = 4;
VD_CHECKED = 0; % default
SHADE_TYPE = 1; % default
grid_drawing;
% to escape recalculation of Okada half space
if IACT ~= 1        
Okada_halfspace;
end
IACT = 1;           % to keep okada output
    a = DC3D(:,1:2);
    b = DC3D(:,5:8);
    c = horzcat(a,b);
    format long;
    % save Displacement.cou a -ascii
    if OUTFLAG == 1 | isempty(OUTFLAG) == 1
	cd output_files;
    else
	cd (PREF_DIR);
    end
    header1 = ['Input file selected: ',INPUT_FILE];
    header2 = 'x y z UX UY UZ';
    header3 = '(km) (km) (km) (m) (m) (m)';
    dlmwrite('Displacement.cou',header1,'delimiter',''); 
    dlmwrite('Displacement.cou',header2,'-append','delimiter',''); 
    dlmwrite('Displacement.cou',header3,'-append','delimiter',''); 
    dlmwrite('Displacement.cou',c,'-append','delimiter','\t','precision','%.8f');
    disp(['Displacement.cou is saved in ' pwd]);
    cd (HOME_DIR);
displ_open(2);
fault_overlay;
flag = check_lonlat_info;
if flag == 1
    all_overlay_enable_on;
%    set(findobj('Tag','menu_focal_mech'),'Enable','On');
end
% ----- overlay drawing --------------------------------
%if ICOORD == 2 && isempty(LON_GRID) ~= 1
    if isempty(COAST_DATA)~=1 | isempty(EQ_DATA)~=1 |...
            isempty(AFAULT_DATA)~=1 | isempty(GPS_DATA)~=1
        figure(H_MAIN); hold on;
        overlay_drawing;
end

%-------------------------------------------------------------------------
%                       3D IMAGE (sub-submenu)
%-------------------------------------------------------------------------
function menu_3d_Callback(hObject, eventdata, handles)
global FUNC_SWITCH
global DC3D IACT INPUT_FILE ICOORD LON_GRID
global OUTFLAG PREF_DIR HOME_DIR H_VIEWPOINT
subfig_clear;
FUNC_SWITCH = 5;
if ICOORD == 2 && isempty(LON_GRID) ~= 1
    h = warndlg('Sorry faults would be invisible so far. To see complete view, change to Cartesian coordinates.',...
        '!! Warning !!');
    waitfor(h);
end
% to escape recalculation of Okada half space
if IACT ~= 1        
Okada_halfspace;
end
IACT = 1;           % to keep okada output
    a = DC3D(:,1:2);
    b = DC3D(:,5:8);
    c = horzcat(a,b);
    format long;
    if OUTFLAG == 1 | isempty(OUTFLAG) == 1
	cd output_files;
    else
	cd (PREF_DIR);
    end
    header1 = ['Input file selected: ',INPUT_FILE];
    header2 = 'x y z UX UY UZ';
    header3 = '(km) (km) (km) (m) (m) (m)';
    dlmwrite('Displacement.cou',header1,'delimiter',''); 
    dlmwrite('Displacement.cou',header2,'-append','delimiter',''); 
    dlmwrite('Displacement.cou',header3,'-append','delimiter',''); 
    dlmwrite('Displacement.cou',c,'-append','delimiter','\t','precision','%.8f');
    disp(['Displacement.cou is saved in ' pwd]);
    cd (HOME_DIR);
grid_drawing_3d; hold on;
displ_open(2);
h = findobj('Tag','xlines'); delete(h);
h = findobj('Tag','ylines'); delete(h);
% FUNC_SWITCH = 0; %reset
% H_VIEWPOINT = viewpoint3d_window;

% --------------------------------------------------------------------
function menu_3d_wire_Callback(hObject, eventdata, handles)
global FUNC_SWITCH
global DC3D IACT INPUT_FILE ICOORD LON_GRID
global OUTFLAG PREF_DIR HOME_DIR H_VIEWPOINT
subfig_clear;
FUNC_SWITCH = 5.5;
if ICOORD == 2 && isempty(LON_GRID) ~= 1
    h = warndlg('Sorry faults would be invisible so far. To see complete view, change to Cartesian coordinates.',...
        '!! Warning !!');
    waitfor(h);
end
% to escape recalculation of Okada half space
if IACT ~= 1        
Okada_halfspace;
end
IACT = 1;           % to keep okada output
    a = DC3D(:,1:2);
    b = DC3D(:,5:8);
    c = horzcat(a,b);
    format long;
    if OUTFLAG == 1 | isempty(OUTFLAG) == 1
	cd output_files;
    else
	cd (PREF_DIR);
    end
    header1 = ['Input file selected: ',INPUT_FILE];
    header2 = 'x y z UX UY UZ';
    header3 = '(km) (km) (km) (m) (m) (m)';
    dlmwrite('Displacement.cou',header1,'delimiter',''); 
    dlmwrite('Displacement.cou',header2,'-append','delimiter',''); 
    dlmwrite('Displacement.cou',header3,'-append','delimiter',''); 
    dlmwrite('Displacement.cou',c,'-append','delimiter','\t','precision','%.8f');
    disp(['Displacement.cou is saved in ' pwd]);
    cd (HOME_DIR);

grid_drawing_3d; hold on;
displ_open(2);
h = findobj('Tag','xlines'); delete(h);
h = findobj('Tag','ylines'); delete(h);
% FUNC_SWITCH = 0; %reset
% H_VIEWPOINT = viewpoint3d_window;

% --------------------------------------------------------------------
function menu_3d_vectors_Callback(hObject, eventdata, handles)
global FUNC_SWITCH
global DC3D IACT INPUT_FILE ICOORD LON_GRID
global OUTFLAG PREF_DIR HOME_DIR H_VIEWPOINT
subfig_clear;
FUNC_SWITCH = 5.7;
if ICOORD == 2 && isempty(LON_GRID) ~= 1
    h = warndlg('Sorry faults would be invisible so far. To see complete view, change to Cartesian coordinates.',...
        '!! Warning !!');
    waitfor(h);
end
% to escape recalculation of Okada half space
if IACT ~= 1        
Okada_halfspace;
end
IACT = 1;           % to keep okada output
    a = DC3D(:,1:2);
    b = DC3D(:,5:8);
    c = horzcat(a,b);
    format long;
    if OUTFLAG == 1 | isempty(OUTFLAG) == 1
	cd output_files;
    else
	cd (PREF_DIR);
    end
    header1 = ['Input file selected: ',INPUT_FILE];
    header2 = 'x y z UX UY UZ';
    header3 = '(km) (km) (km) (m) (m) (m)';
    dlmwrite('Displacement.cou',header1,'delimiter',''); 
    dlmwrite('Displacement.cou',header2,'-append','delimiter',''); 
    dlmwrite('Displacement.cou',header3,'-append','delimiter',''); 
    dlmwrite('Displacement.cou',c,'-append','delimiter','\t','precision','%.8f');
    disp(['Displacement.cou is saved in ' pwd]);
    cd (HOME_DIR);
grid_drawing_3d; hold on;
displ_open(2);
h = findobj('Tag','xlines'); delete(h);
h = findobj('Tag','ylines'); delete(h);
% FUNC_SWITCH = 0; %reset
% H_VIEWPOINT = viewpoint3d_window;

%-------------------------------------------------------------------------
%           STRAIN (submenu)     
%-------------------------------------------------------------------------
function menu_strain_Callback(hObject, eventdata, handles)
global H_STRAIN IACT H_MAIN
global FUNC_SWITCH SHADE_TYPE STRAIN_SWITCH
global COAST_DATA EQ_DATA AFAULT_DATA GPS_DATA
subfig_clear;   IACT = 0;
FUNC_SWITCH = 6;
SHADE_TYPE = 1; % default
STRAIN_SWITCH = 1; % default sig XX
H_STRAIN = strain_window;
flag = check_lonlat_info;
if flag == 1
    all_overlay_enable_on;
%    set(findobj('Tag','menu_focal_mech'),'Enable','On');
end
% ----- overlay drawing --------------------------------
%if ICOORD == 2 && isempty(LON_GRID) ~= 1
    if isempty(COAST_DATA)~=1 | isempty(EQ_DATA)~=1 |...
            isempty(AFAULT_DATA)~=1 | isempty(GPS_DATA)~=1
        figure(H_MAIN); hold on;
        overlay_drawing;
end

%-------------------------------------------------------------------------
%           STRESS (submenu)        with sub-submenu
%-------------------------------------------------------------------------
function menu_stress_Callback(hObject, eventdata, handles)

% --------------------------------------------------------------------
function menu_shear_stress_change_Callback(hObject, eventdata, handles)
global FUNC_SWITCH IACT
global STRESS_TYPE
global H_COULOMB
subfig_clear;   IACT = 0;
FUNC_SWITCH = 7;    STRESS_TYPE = 5;
H_COULOMB = coulomb_window;
set(findobj('Tag','text_fric'),'Visible','off');
set(findobj('Tag','edit_coul_fric'),'Visible','off');
flag = check_lonlat_info;
if flag == 1
    all_overlay_enable_on;
%    set(findobj('Tag','menu_focal_mech'),'Enable','On');
end

% --------------------------------------------------------------------
function menu_normal_stress_change_Callback(hObject, eventdata, handles)
global FUNC_SWITCH IACT
global STRESS_TYPE
global H_COULOMB
subfig_clear;   IACT = 0;
FUNC_SWITCH = 8;    STRESS_TYPE = 5;
H_COULOMB = coulomb_window;
set(findobj('Tag','text_fric'),'Visible','off');
set(findobj('Tag','edit_coul_fric'),'Visible','off');
flag = check_lonlat_info;
if flag == 1
    all_overlay_enable_on;
%    set(findobj('Tag','menu_focal_mech'),'Enable','On');
end

% --------------------------------------------------------------------
function menu_coulomb_stress_change_Callback(hObject, eventdata, handles)
global FUNC_SWITCH IACT
global STRESS_TYPE
global H_COULOMB
subfig_clear;   IACT = 0;
FUNC_SWITCH = 9;    STRESS_TYPE = 5;
H_COULOMB = coulomb_window;
set(findobj('Tag','crosssection_toggle'),'Enable','off');
flag = check_lonlat_info;
if flag == 1
    all_overlay_enable_on;
%    set(findobj('Tag','menu_focal_mech'),'Enable','On');
end

% --------------------------------------------------------------------
function menu_stress_on_faults_Callback(hObject, eventdata, handles)
global ELEMENT POIS YOUNG FRIC ID
global FUNC_SWITCH ICOORD LON_GRID
global h_grid
global DC3D IACT
global H_MAIN H_EC_CONTROL H_VIEWPOINT
if ICOORD == 2 && isempty(LON_GRID) ~= 1
    h = warndlg('Sorry this is not available for lat/lon coordinates. Change to Cartesian coordinates.',...
        '!! Warning !!');
    waitfor(h);
    return
end
% hc = wait_calc_window;   % custom waiting dialog
subfig_clear;
% clear_obj_and_subfig
FUNC_SWITCH = 10;
% element_condition(ELEMENT,POIS,YOUNG,FRIC,ID);
% grid_drawing_3d;
% displ_open(2);
H_EC_CONTROL = ec_control_window;
% close(hc);

% --------------------------------------------------------------------
function menu_stress_on_a_fault_Callback(hObject, eventdata, handles)
global FUNC_SWITCH H_POINT IACT
IACT = 0;
if FUNC_SWITCH ~= 7 && FUNC_SWITCH ~= 8 && FUNC_SWITCH ~= 9
    subfig_clear;
    FUNC_SWITCH = 1;
    grid_drawing;
    fault_overlay;
end
H_POINT = point_calc_window;
flag = check_lonlat_info;
if flag == 1
    all_overlay_enable_on;
%    set(findobj('Tag','menu_focal_mech'),'Enable','On');
end

% --------------------------------------------------------------------
function menu_focal_mech_Callback(hObject, eventdata, handles)
global FUNC_SWITCH NODAL_ACT NODAL_STRESS HOME_DIR
FUNC_SWITCH = 11;
NODAL_ACT = 0;
NODAL_STRESS = [];
cd (HOME_DIR);
focal_mech_calc;

%-------------------------------------------------------------------------
%           CHANGE PARAMETERS (submenu) 
%-------------------------------------------------------------------------
function menu_change_parameters_Callback(hObject, eventdata, handles)

% --------------------------------------------------------------------
function menu_all_parameters_Callback(hObject, eventdata, handles)
global H_INPUT IACT
H_INPUT = input_window;
waitfor(H_INPUT);
IACT = 0;
menu_grid_mapview_Callback;     % redraw the renewed grid

% --------------------------------------------------------------------
function menu_grid_size_Callback(hObject, eventdata, handles)
global GRID
global IACT ICOORD LON_GRID LON_PER_X LAT_PER_Y XY_RATIO
temp1 = GRID(5,1); temp2 = GRID(6,1);
if ICOORD == 2 && isempty(LON_GRID) ~= 1
    prompt = {'Enter new lon. increment(deg):','Enter new lat. increment(deg):'};
    defc1 = num2str(GRID(5,1)*LON_PER_X,'%9.3f');
    defc2 = num2str(GRID(6,1)*LAT_PER_Y,'%9.3f');
else
    prompt = {'Enter new x increment(km):','Enter new y increment(km):'};
    defc1 = num2str(GRID(5,1),'%9.3f');
    defc2 = num2str(GRID(6,1),'%9.3f');
end
name = 'Grid Size';
numlines = 1;
options.Resize = 'on';
options.WindowStyle = 'normal';
answer = inputdlg(prompt,name,numlines,{defc1,defc2},options);
answer = [answer];
    n = 5;
    xlim = (GRID(3)-GRID(1))/n;
    ylim = (GRID(4)-GRID(2))/n;
if ICOORD == 2 && isempty(LON_GRID) ~= 1
    GRID(5,1) = str2double(answer(1))/LON_PER_X;
    GRID(6,1) = str2double(answer(2))/LAT_PER_Y;
    xlim = xlim/LON_PER_X;
    ylim = ylim/LAT_PER_Y;
else
    GRID(5,1) = str2double(answer(1));
    GRID(6,1) = str2double(answer(2));
end
if str2double(answer(1)) > xlim
    warndlg('The x increment might be large relative to the study area. Not acceptable.');
    return
end
if str2double(answer(2)) > xlim
    warndlg('The y increment might be large relative to the study area. Not acceptable.');
    return
end
if isnan(GRID(5,1)) == 1 | isempty(GRID(5,1)) == 1
    GRID(5,1) = temp1;
end
if isnan(GRID(6,1)) == 1 | isempty(GRID(6,1)) == 1
    GRID(6,1) = temp2;
end
% to calculate and save numbers for basic info
calc_element;
IACT = 0;
menu_grid_mapview_Callback;     % redraw the renewed grid

% --------------------------------------------------------------------
function menu_calc_depth_Callback(hObject, eventdata, handles)
global CALC_DEPTH
global IACT
global H_DISPL
temp = CALC_DEPTH;
prompt = 'Enter new calculation depth (positive):';
name = 'Calc. Depth';
numlines = 1;
options.Resize = 'on';
options.WindowStyle = 'normal';
defc = num2str(CALC_DEPTH,'%6.2f');
answer = inputdlg(prompt,name,numlines,{defc},options);
if str2double(answer) < 0.0
    warndlg('Put positive number. Not acceptable');
	return
end
CALC_DEPTH = str2double(answer);
if isnan(CALC_DEPTH) == 1 | isempty(CALC_DEPTH) == 1
    CALC_DEPTH = temp;
end
h = findobj('Tag','displ_h_window');
if (isempty(h)~=1 && isempty(H_DISPL)~=1)
    set(findobj('Tag','edit_displdepth'),'String',num2str(CALC_DEPTH,'%5.2f'));
end
IACT = 0;
menu_grid_mapview_Callback;     % redraw the renewed grid

% --------------------------------------------------------------------
function menu_coeff_friction_Callback(hObject, eventdata, handles)
global FRIC
temp = FRIC;
prompt = 'Enter new friction (positive):';
name = 'Coeff. Friction';
numlines = 1;
options.Resize = 'on';
options.WindowStyle = 'normal';
defc = num2str(FRIC,'%4.3f')
answer = inputdlg(prompt,name,numlines,{defc},options);
if str2double(answer) < 0.0
    warndlg('Put positive number. Not acceptable');
	return
end
FRIC = str2double(answer);
if isnan(FRIC) == 1 | isempty(FRIC) == 1
    FRIC = temp;
end

% --------------------------------------------------------------------
function menu_exaggeration_Callback(hObject, eventdata, handles)
global SIZE
temp = SIZE(3);
prompt = 'Enter new displ. exaggeration:';
name = 'Displ. exaggeration';
numlines = 1;
options.Resize = 'on';
options.WindowStyle = 'normal';
defc = num2str(SIZE(3));
answer = inputdlg(prompt,name,numlines,{defc},options);
SIZE(3) = str2double(answer);
if isnan(SIZE(3)) == 1 | isempty(SIZE(3)) == 1
    SIZE(3) = temp;
end

%-------------------------------------------------------------------------
%           TAPER & SPLIT (submenu) 
%-------------------------------------------------------------------------
function menu_taper_split_Callback(hObject, eventdata, handles)
global H_ELEMENT TAPER_CALLED
H_ELEMENT = element_input_window;
TAPER_CALLED = 1;

%-------------------------------------------------------------------------
%           CALC. CARTESIAN GRID (submenu) 
%-------------------------------------------------------------------------
function menu_cartesian_Callback(hObject, eventdata, handles)
global H_UTM
global UTM_FLAG  % UTM_FLAG is used to identify if this is just a tool to know the coordinate (0) or
                 % to make an input file from this (1)
%===== see if user has mapping toolbox or not ========
if exist([matlabroot '/toolbox/map'],'dir')==0
    warndlg('Since you do not have mapping toolbox, this menu is unavailable. Sorry.',...
        '!!Warning!!');
    return;
end
H_UTM = utm_window;
UTM_FLAG = 0; % just a tool
set(findobj('Tag','pushbutton_add'),'Visible','off');
set(findobj('Tag','pushbutton_f_add'),'Visible','off');
set(findobj('Tag','edit_all_input_params'),'Visible','off');

%-------------------------------------------------------------------------
%           CALC. PROPER PRINCIPAL AXES (submenu) 
%-------------------------------------------------------------------------
function menu_calc_principal_Callback(hObject, eventdata, handles)
global H_CALC_PRINCIPAL
H_CALC_PRINCIPAL = calc_principals_window;

%-------------------------------------------------------------------------
%           HELP (submenu) 
%-------------------------------------------------------------------------
function menu_help_Callback(hObject, eventdata, handles)
global H_HELP
H_HELP = coulomb_help_window;
% hObject    handle to menu_help (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

%=========================================================================
%    OVERLAY (menu)
%=========================================================================
function overlay_menu_Callback(hObject, eventdata, handles)

%-------------------------------------------------------------------------
%           COASTLINES (submenu) 
%-------------------------------------------------------------------------
function menu_coastlines_Callback(hObject, eventdata, handles)
global H_MAIN COAST_DATA
    if strcmp(get(gcbo, 'Checked'),'on')
        set(gcbo, 'Checked', 'off');
        figure(H_MAIN);        
        try
            h = findobj('Tag','CoastlineObj');
            delete(h);
        catch
            return
        end
    else 
        set(gcbo, 'Checked', 'on');
        hold off;
        coastline_drawing;
        hold on;
    end

%-------------------------------------------------------------------------
%           ACTIVE FAULTS (submenu) 
%-------------------------------------------------------------------------
function menu_activefaults_Callback(hObject, eventdata, handles)
global H_MAIN AFAULT_DATA
    if strcmp(get(gcbo, 'Checked'),'on')
        set(gcbo, 'Checked', 'off');
        figure(H_MAIN);
        try
            h = findobj('Tag','AfaultObj');
            delete(h);
        catch
            return
        end
    else 
        set(gcbo, 'Checked', 'on');
        hold off;
        if isempty(AFAULT_DATA) == 1
            afault_format_window;
        else
 %           hold off;
            afault_drawing;
        end
        hold on;
    end
    
%-------------------------------------------------------------------------
%           EARTHQUAKES (submenu) 
%-------------------------------------------------------------------------
function menu_earthquakes_Callback(hObject, eventdata, handles)
global H_MAIN H_F3D_VIEW H_EC_CONTROL
    if strcmp(get(gcbo, 'Checked'),'on')
        set(gcbo, 'Checked', 'off');
        figure(H_MAIN);
        try
            h = findobj('Tag','EqObj');
            delete(h);
        catch
            return
        end
        try
            h = findobj('Tag','EqObj2');
            delete(h);
        catch
            return
        end
    else 
        set(gcbo, 'Checked', 'on');
        hold off;
        earthquake_plot;
%         if ~isempty(H_F3D_VIEW) | ~isempty(H_EC_CONTROL)
%             
%         else
            fault_overlay;  % plot fault again
%         end
        hold on;
    end


%-------------------------------------------------------------------------
%           VOLCANOES (submenu) 
%-------------------------------------------------------------------------
function menu_volcanoes_Callback(hObject, eventdata, handles)
global H_MAIN PREF
    if strcmp(get(gcbo, 'Checked'),'on')
        set(gcbo, 'Checked', 'off');
        figure(H_MAIN);
        try
            h = findobj('Tag','VolcanoObj');
            delete(h);
        catch
            return
        end
    else 
        set(gcbo, 'Checked', 'on');
        hold off;
        volcano_overlay('MarkerSize',PREF(9,4)*14);
        hold on;
    end

    
%-------------------------------------------------------------------------
%           GPS stations (submenu) 
%-------------------------------------------------------------------------
function menu_gps_Callback(hObject, eventdata, handles)
global H_MAIN ICOORD LON_GRID PREF
global H_F3D_VIEW % identifier if the graphic is 2D or 3D
global GPS_DATA SIZE

%     ck = get(findobj('Tag','menu_gps'),'Checked'); 
   if strcmp(get(gcbo, 'Checked'),'on')
%     if strcmp(ck,'on')
        set(gcbo, 'Checked', 'off');
        set(findobj('Tag','menu_gps'),'Checked','off'); 
        figure(H_MAIN);
        try
            delete(findobj('Tag','GPSObj'));
            delete(findobj('Tag','GPSOBSObj'));
            delete(findobj('Tag','GPSCALCObj'));
            delete(findobj('Tag','UNITObj'));
            delete(findobj('Tag','UNITTEXTObj'));
            delete(findobj('Tag','GPS3D_OBS_Obj'));
            delete(findobj('Tag','GPS3D_CALC_Obj'));
        catch
            return
        end
    else 
        set(gcbo, 'Checked', 'on');
%         set(findobj('Tag','menu_gps'),'Checked','on'); 
        hold off;
        if isempty(H_F3D_VIEW)
            gps_plot;
            fault_overlay;  % plot fault again
        else
            % h = findobj('Tag','menu_gps');
            % h1 = get(h,'Checked');
            
            gps_3d_overlay;
%             if ~isempty(GPS_DATA)
%                 zero = zeros(size(GPS_DATA,1),1);
%                 hold on;
% %                 if ICOORD == 2 && isempty(LON_GRID) ~= 1                % lon.lat.coordinates
% %                 h = scatter3(GPS_DATA(:,1),GPS_DATA(:,2),zero,5*PREF(5,4));
% %                 else
%                 h = scatter3(GPS_DATA(:,6),GPS_DATA(:,7),zero,5*PREF(5,4));
%                 hold on;
%                 h1 = quiver3(GPS_DATA(:,6),GPS_DATA(:,7),zero,...
%                     GPS_DATA(:,3)*SIZE(3),...
%                     GPS_DATA(:,4)*SIZE(3),...
%                     GPS_DATA(:,5)*SIZE(3),...
%                     'Color','b');
%                 % calc in half space
%                     m = size(GPS_DATA(:,6),1);
%                     ux = zeros(m,1,'double');
%                     uy = zeros(m,1,'double');
%                     uz = zeros(m,1,'double');
%                     [dc3de] = dc3de_calc(GPS_DATA(:,6),GPS_DATA(:,7));
%                     ux = dc3de(:,6);
%                     uy = dc3de(:,7);
%                     uz = dc3de(:,8);
%                     hold on;
%                     h2 = quiver3(GPS_DATA(:,6),GPS_DATA(:,7),zero,...
%                                 ux*SIZE(3),...
%                                 uy*SIZE(3),...
%                                 uz*SIZE(3),...
%                                 'Color','r');
%                     set(h1,'Tag','GPS3D_OBS_Obj');
%                     set(h2,'Tag','GPS3D_CALC_Obj');
%                 %
% %                 end
%                 set(h,'MarkerEdgeColor',[0.1,0.2,0.9]); % white edge color for GPS station 
%                 set(h,'Tag','GPSObj');        % put a tag to remove them later
%                 hold on;
%             end

        end
        hold on;
   end

%-------------------------------------------------------------------------
%           Trace faults and put them into input file (submenu) 
%-------------------------------------------------------------------------
function menu_trace_put_faults_Callback(hObject, eventdata, handles)
new_fault_mouse_clicks;

%----------------------------------------------------------
function all_functions_enable_on
set(findobj('Tag','menu_grid'),'Enable','On');
set(findobj('Tag','menu_displacement'),'Enable','On');
set(findobj('Tag','menu_strain'),'Enable','On');
set(findobj('Tag','menu_stress'),'Enable','On');
set(findobj('Tag','menu_change_parameters'),'Enable','On');
set(findobj('Tag','menu_taper_split'),'Enable','On');

%----------------------------------------------------------
function all_functions_enable_off
set(findobj('Tag','menu_grid'),'Enable','Off');
set(findobj('Tag','menu_displacement'),'Enable','Off');
set(findobj('Tag','menu_strain'),'Enable','Off');
set(findobj('Tag','menu_stress'),'Enable','Off');
set(findobj('Tag','menu_taper_split'),'Enable','Off');

%----------------------------------------------------------
function all_overlay_enable_on
set(findobj('Tag','menu_coastlines'),'Enable','On');
set(findobj('Tag','menu_activefaults'),'Enable','On');
set(findobj('Tag','menu_earthquakes'),'Enable','On');
set(findobj('Tag','menu_volcanoes'),'Enable','On');
set(findobj('Tag','menu_gps'),'Enable','On'); 
set(findobj('Tag','menu_clear_overlay'),'Enable','On');
set(findobj('Tag','menu_trace_put_faults'),'Enable','On'); 

%----------------------------------------------------------
function all_overlay_enable_off
set(findobj('Tag','menu_coastlines'),'Enable','Off');
set(findobj('Tag','menu_activefaults'),'Enable','Off');
set(findobj('Tag','menu_earthquakes'),'Enable','Off');
set(findobj('Tag','menu_volcanoes'),'Enable','Off');
set(findobj('Tag','menu_gps'),'Enable','Off'); 
set(findobj('Tag','menu_clear_overlay'),'Enable','Off'); 
set(findobj('Tag','menu_trace_put_faults'),'Enable','Off'); 

% % --------------------------------------------------------------------
function menu_tools_Callback(hObject, eventdata, handles)
% % hObject    handle to menu_tools (see GCBO)
% % eventdata  reserved - to be defined in a future version of MATLAB
% % handles    structure with handles and user data (see GUIDATA)


%-------------------------------------------------------------------------
%	Clear overlay data (submenu) 
%-------------------------------------------------------------------------
function menu_clear_overlay_Callback(hObject, eventdata, handles)
% hObject    handle to menu_clear_overlay (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
global COAST_DATA AFAULT_DATA EQ_DATA GPS_DATA
global VOLCANO
if isempty(COAST_DATA)==1
    set(findobj('Tag','submenu_clear_coastlines'),'Enable','Off');
else
    set(findobj('Tag','submenu_clear_coastlines'),'Enable','On');
end
if isempty(AFAULT_DATA)==1
    set(findobj('Tag','submenu_clear_afaults'),'Enable','Off');
else
    set(findobj('Tag','submenu_clear_afaults'),'Enable','On');
end
if isempty(EQ_DATA)==1
    set(findobj('Tag','submenu_clear_earthquakes'),'Enable','Off');
else
    set(findobj('Tag','submenu_clear_earthquakes'),'Enable','On');
end
if isempty(VOLCANO)==1
    set(findobj('Tag','submenu_clear_volcanoes'),'Enable','Off');
else
    set(findobj('Tag','submenu_clear_volcanoes'),'Enable','On');
end
if isempty(GPS_DATA)==1
    set(findobj('Tag','submenu_clear_gps'),'Enable','Off');
else
    set(findobj('Tag','submenu_clear_gps'),'Enable','On');
end

%-------------------------------------------------------------------------
%       Submenu clear coastline data (submenu) 
%-------------------------------------------------------------------------
function submenu_clear_coastlines_Callback(hObject, eventdata, handles)
global COAST_DATA H_MAIN
COAST_DATA = [];
set(findobj('Tag','menu_coastlines'),'Checked','Off');
        figure(H_MAIN);        
        try
            h = findobj('Tag','CoastlineObj');
            delete(h);
        catch
            return
        end
% hObject    handle to submenu_clear_coastlines (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

%-------------------------------------------------------------------------
%       Submenu clear active fault data (submenu) 
%-------------------------------------------------------------------------
function submenu_clear_afaults_Callback(hObject, eventdata, handles)
global AFAULT_DATA H_MAIN
AFAULT_DATA = [];
set(findobj('Tag','menu_activefaults'),'Checked','Off');
        figure(H_MAIN);        
        try
            h = findobj('Tag','AfaultObj');
            delete(h);
        catch
            return
        end
% hObject    handle to submenu_clear_afaults (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

%-------------------------------------------------------------------------
%       Submenu clear earthquake data (submenu) 
%-------------------------------------------------------------------------
function submenu_clear_earthquakes_Callback(hObject, eventdata, handles)
global EQ_DATA H_MAIN
EQ_DATA = [];
set(findobj('Tag','menu_earthquakes'),'Checked','Off');
set(findobj('Tag','menu_focal_mech'),'Enable','Off');
        figure(H_MAIN);        
        try
            h = findobj('Tag','EqObj');
            delete(h);
        catch
            return
        end
        try
            h = findobj('Tag','EqObj2');
            delete(h);
        catch
            return
        end

% hObject    handle to submenu_clear_earthquakes (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

%-------------------------------------------------------------------------
%       Submenu clear volcano data (submenu) 
%-------------------------------------------------------------------------
function submenu_clear_volcanoes_Callback(hObject, eventdata, handles)
global VOLCANO H_MAIN
VOLCANO = [];
set(findobj('Tag','menu_volcanoes'),'Checked','Off');
        figure(H_MAIN);        
        try
            h = findobj('Tag','VolcanoObj');
            delete(h);
        catch
            return
        end

%-------------------------------------------------------------------------
%       Submenu clear gps data (submenu) 
%-------------------------------------------------------------------------
function submenu_clear_gps_Callback(hObject, eventdata, handles)
global GPS_DATA H_MAIN
GPS_DATA = [];
set(findobj('Tag','menu_gps'),'Checked','Off');
        figure(H_MAIN);        
        try
            delete(findobj('Tag','GPSObj'));
            delete(findobj('Tag','GPSOBSObj'));
            delete(findobj('Tag','GPSCALCObj'));
            delete(findobj('Tag','UNITObj'));
            delete(findobj('Tag','UNITTEXTObj'));
        catch
            return
        end
% hObject    handle to submenu_clear_earthquakes (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

% --------------------------------------------------------------------
function uimenu_fault_modifications_Callback(hObject, eventdata, handles)
% hObject    handle to uimenu_fault_modifications (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)
disp('under construction')

% --------------------------------------------------------------------
function Context_functions_Callback(hObject, eventdata, handles)
% hObject    handle to Context_functions (see GCBO)
% eventdata  reserved - to be defined in a future version of MATLAB
% handles    structure with handles and user data (see GUIDATA)

function check_overlay_items
global COAST_DATA AFAULT_DATA EQ_DATA GPS_DATA
global VOLCANO
    if ~isempty(COAST_DATA)
        set(findobj('Tag','menu_coastlines'),'Checked','On');
    else
        set(findobj('Tag','menu_coastlines'),'Checked','Off');
    end
    if ~isempty(AFAULT_DATA)
        set(findobj('Tag','menu_activefaults'),'Checked','On');
    else
        set(findobj('Tag','menu_activefaults'),'Checked','Off');
    end
    if ~isempty(EQ_DATA)
        set(findobj('Tag','menu_earthquakes'),'Checked','On');
    else
        set(findobj('Tag','menu_earthquakes'),'Checked','Off');
    end
    if ~isempty(VOLCANO)
        set(findobj('Tag','menu_volcanoes'),'Checked','On');
    else
        set(findobj('Tag','menu_volcanoes'),'Checked','Off');
    end
    if ~isempty(GPS_DATA)
        set(findobj('Tag','menu_gps'),'Checked','On');
    else
        set(findobj('Tag','menu_gps'),'Checked','Off');
    end
    



