function grid_drawing
% grid mesh drawing function for grid option
% This function frequently used as a basemap for the other plotting
% functions.
% 
%   coded by Shinji Toda
%

global GRID
global XGRID YGRID INPUT_FILE
global H_MAIN A_GRID
global FUNC_SWITCH CALC_DEPTH FRIC
global PREF
global ICOORD LON_GRID XY_RATIO CURRENT_VERSION

xstart = GRID(1,1);
ystart = GRID(2,1);
xfinish = GRID(3,1);
yfinish = GRID(4,1);
% XY_RATIO = 1.0;         % default (to adjust aspect ratio)
if ICOORD == 2 && isempty(LON_GRID) ~= 1
    a  = xy2lonlat([GRID(1,1) GRID(2,1)]);
    xstart = a(1);
    ystart = a(2);
    a = xy2lonlat([GRID(3,1) GRID(4,1)]);
    xfinish = a(1);
    yfinish = a(2);
else
    XY_RATIO = 1;
end

figure(H_MAIN);
set(H_MAIN,'Menubar','figure','Toolbar','figure');
set(H_MAIN,'Renderer','Painters');
hold off;

    A_GRID = plot([xstart xfinish xfinish xstart xstart],...
    [ystart ystart yfinish yfinish ystart]);
    set(gca,'DataAspectRatio',[XY_RATIO 1 1],...
    'Color',[0.9 0.9 0.9],...
    'PlotBoxAspectRatio',[1 1 1],...
    'XLim',[xstart,xfinish],...
    'YLim',[ystart,yfinish]);
    h = get(gca,'Parent');
    hx = xlabel('X (km)');
    hy = ylabel('Y (km)');
	set(hx,'FontSize',[14]);
	set(hy,'FontSize',[14]);
    
if PREF(3,4)~=0.0 % if GRID line width is 0.0, skip the following block.   
for m = 1:length(XGRID)
    hold on;
% lat/lon coordinata (ICOORD == 2)
    if ICOORD == 2 && isempty(LON_GRID) ~= 1
        a = xy2lonlat([XGRID(m) ystart]); % ystart is dummy
        gridln1 = plot([a(1) a(1)],[ystart yfinish]);
    else
% x/y coordinate (ICOORD == 1)
        gridln1 = plot([XGRID(m) XGRID(m)],[ystart yfinish]);
    end
    if FUNC_SWITCH == 1 | FUNC_SWITCH == 11
        set(gridln1,'LineWidth',PREF(3,4),'Color',PREF(3,1:3));
    elseif FUNC_SWITCH == 2 | FUNC_SWITCH == 3
        set(gridln1,'LineWidth',PREF(3,4),'Color',PREF(3,1:3));
    end
end

for n = 1:length(YGRID)
    hold on;
    if ICOORD == 2 && isempty(LON_GRID) ~= 1
        a = xy2lonlat([xstart YGRID(n)]); % xstart is dummy
        gridln2 = plot([xstart xfinish],[a(2) a(2)]);
    else
        gridln2 = plot([xstart xfinish],[YGRID(n) YGRID(n)]);
    end
    if FUNC_SWITCH == 1 | FUNC_SWITCH == 11
        set(gridln2,'LineWidth',PREF(3,4),'Color',PREF(3,1:3));
    elseif FUNC_SWITCH == 2 | FUNC_SWITCH == 3
        set(gridln2,'LineWidth',PREF(3,4),'Color',PREF(3,1:3));
    end
end
end

% repetition ???
hold on;
% Define the context menu
    cmenu = uicontextmenu;
    
	A_GRID = plot([xstart xfinish xfinish xstart xstart],...
    [ystart ystart yfinish yfinish ystart]);
    set(gca,'DataAspectRatio',[XY_RATIO 1 1],...
    'Color',[0.9 0.9 0.9],...
    'PlotBoxAspectRatio',[1 1 1],...
    'XLim',[xstart,xfinish],...
    'YLim',[ystart,yfinish],'UIContextMenu', cmenu);
    h = get(gca,'Parent');
    if ICOORD == 2 && isempty(LON_GRID) ~= 1
    	hx = xlabel('Longitude (degree)');
        hy = ylabel('Latitude  (degree)');
    else
        hx = xlabel('X (km)');
        hy = ylabel('Y (km)');
    end
	set(hx,'FontSize',[14]);
	set(hy,'FontSize',[14]);

    % Define the context menu items
items1 = uimenu(cmenu, 'Label', 'change study area',...
    'Callback','change_study_area');
items2 = uimenu(cmenu, 'Label', 'change coordinates',...
    'Callback','change_coordinates');

%----------- data & file name stamp --------------
hold on;
r = (yfinish-ystart)/(xfinish-xstart);
if r > 1
    r = 1;
end
x = xfinish + ((xfinish-xstart)/(10.0/r));
y = ystart - ((yfinish-ystart)/10.0) / r;
lsp = ((xfinish-xstart)+(yfinish-ystart))/75.0;
% date_and_file_stamp(H_MAIN,INPUT_FILE,x,y,lsp,FUNC_SWITCH,CALC_DEPTH);
try
record_stamp(H_MAIN,x,y,'SoftwareVersion',CURRENT_VERSION,...
        'FunctionType',FUNC_SWITCH,'Depth',CALC_DEPTH,'Friction',FRIC,...
        'FileName',INPUT_FILE,'LineSpace',lsp,...
        'FontSize',9);
catch
record_stamp(H_MAIN,x,y,'SoftwareVersion',CURRENT_VERSION,...
        'FunctionType',FUNC_SWITCH,'Depth',CALC_DEPTH,...
        'FileName',INPUT_FILE,'LineSpace',lsp,...
        'FontSize',9);
end

set(H_MAIN,'PaperPositionMode','auto');

hold off;

